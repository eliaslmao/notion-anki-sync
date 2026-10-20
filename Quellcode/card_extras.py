"""Safe metadata sections and per-gap inline input payloads/templates."""
import copy
import html
import json
import re
from html.parser import HTMLParser
from .core import SyncError

HEADER_MARK = '<!-- ns-header-v1 -->'
HEADER_TEMPLATE = HEADER_MARK+'{{#Header}}<details class="ns-header"><summary>Mehr …</summary><div>{{Header}}</div></details>{{/Header}}'
HEADER_CSS = '.ns-header{margin-top:clamp(3em,8vw,4.5em);padding-top:1em;border-top:1px solid #8886;font-size:.85em}.ns-header summary{cursor:pointer;display:list-item}.ns-header>div{margin:.75em 0;overflow-wrap:anywhere}'
HEADER_STYLE_MARK = '/* ns-header-spacing-v2 */'


def inert_braces(text):
    # Anki scans note fields for cloze numbers, including non-question fields.
    # Entities render literally but cannot create cards from metadata/answers.
    return text.replace('{','&#123;').replace('}','&#125;')


def drop_prefix(items,count):
    remaining = []
    for item in items:
        text = item.get('plain_text',item.get('text',{}).get('content',''))
        if count>=len(text):
            count -= len(text)
            continue
        value = copy.deepcopy(item)
        if count:
            if value.get('type')!='text': raise SyncError('Metadatenmarker muss normaler Text sein.')
            value['text']['content'] = text[count:]
            value.pop('plain_text',None)
            count = 0
        remaining.append(value)
    return remaining


def split_header(children,renderer):
    main,meta,started = [],[],False
    for block in children:
        if block['type']=='paragraph':
            items = block['paragraph'].get('rich_text',[])
            text = ''.join(i.get('plain_text',i.get('text',{}).get('content','')) for i in items)
            if text.startswith('[Header]'):
                if started: raise SyncError('[Header] darf nur einmal pro Blatt-Toggle vorkommen.')
                started = True
                value = copy.deepcopy(block)
                value['paragraph']['rich_text'] = drop_prefix(items,len('[Header]'))
                meta.append(value)
                continue
        (meta if started else main).append(block)
    return main,inert_braces(''.join(renderer.block(b) for b in meta))


def legacy_header(header):
    return HEADER_MARK+'<details class="ns-header"><summary>Mehr …</summary><div>'+header+'</div></details>' if header else ''


class Text(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.parts=[]
    def handle_data(self,data): self.parts.append(data)
    def handle_starttag(self,tag,attrs):
        if tag=='br': self.parts.append('\n')


def inline_payload(content):
    """Wrap native clozes externally. Native numbering/card generation is intact."""
    index,occurrences = 0,{}
    def parse(start=0,closing=False):
        nonlocal index
        rendered,answer = [],[]
        cursor = start
        while cursor<len(content):
            if content.startswith('}}',cursor) and closing:
                return ''.join(rendered),''.join(answer),cursor+2
            match = re.match(r'\{\{c([1-9]\d*)::',content[cursor:])
            if match:
                key = str(index)
                index += 1
                body,plain_body,end = parse(cursor+len(match[0]),True)
                expected = Text()
                expected.feed(plain_body.split('::',1)[0])
                occurrences[key] = ''.join(expected.parts)
                rendered.append('<span class="ns-gap" data-ns-key="'+key+'" data-ns-id="'+match[1]+'">'+match[0]+body+'}}</span>')
                answer.append(plain_body.split('::',1)[0])
                cursor = end
            else:
                rendered.append(content[cursor]); answer.append(content[cursor]); cursor+=1
        return ''.join(rendered),''.join(answer),cursor
    wrapped,_,_ = parse()
    return wrapped,inert_braces(html.escape(json.dumps(occurrences,ensure_ascii=False,separators=(',',':'))))


INLINE_CSS = '.ns-inline-input{display:inline-block;vertical-align:baseline;width:9em;min-width:3em;max-width:85vw;font:inherit;border:1px solid #888;border-radius:3px;padding:0 .15em}.ns-inline-feedback{font-size:.85em;white-space:normal}.ns-inline-ok{color:#16713a}.ns-inline-wrong{color:#ba2727}'
INLINE_JS = r'''<script>(function(){
var root=document.getElementById('ns-inline-root');if(!root)return;
var data=JSON.parse(root.querySelector('.ns-inline-data').textContent),id=root.querySelector('.ns-inline-id').textContent;
var gaps=Array.from(root.querySelectorAll('.ns-gap')).map(function(g){var c=Array.from(g.querySelectorAll('.cloze')).find(function(x){return x.closest('.ns-gap')===g});return c?{g:g,c:c}:null}).filter(Boolean);
var key=id+':'+gaps.map(function(x){return x.g.dataset.nsId}).join(',');
function norm(x){return String(x).normalize('NFC').replace(/\s+/g,' ').trim()}
if(root.dataset.side==='question'){
 window.nsInlineState={key:key,values:{}};
 gaps.forEach(function(x,i){var input=document.createElement('input');input.type='text';input.className='ns-inline-input';input.autocomplete='off';input.setAttribute('aria-label','Lücke '+(i+1));input.dataset.key=x.g.dataset.nsKey;
 input.addEventListener('input',function(){window.nsInlineState.values[input.dataset.key]=input.value});
 input.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();e.stopPropagation();window.nsInlineState.values[input.dataset.key]=input.value;if(typeof pycmd==='function')pycmd('ans')}});
 x.c.replaceWith(input);if(i===0)setTimeout(function(){input.focus()},80);
 });
}else{
 var state=window.nsInlineState&&window.nsInlineState.key===key?window.nsInlineState.values:{};
 gaps.forEach(function(x){var expected=data[x.g.dataset.nsKey]||'',provided=state[x.g.dataset.nsKey]||'',ok=norm(expected)===norm(provided),feedback=document.createElement('span');feedback.className='ns-inline-feedback '+(ok?'ns-inline-ok':'ns-inline-wrong');feedback.dataset.correct=ok?'1':'0';feedback.textContent=ok?'✓ Richtig':'✗ '+(provided||'Keine Eingabe');feedback.setAttribute('aria-label',ok?'Richtig':'Nicht richtig. Eingabe: '+(provided||'Keine Eingabe')+'. Lösung: '+expected);x.c.after(feedback)});
}
})();</script>'''


def inline_template(side):
    return '<div id="ns-inline-root" data-side="'+side+'"><span class="ns-inline-data" hidden>{{InlineData}}</span><span class="ns-inline-id" hidden>{{NotionID}}</span>{{cloze:Back}}</div>'+INLINE_JS+('{{Extra}}' if side=='answer' else '')


def ensure_features(col,model,kind):
    """Undoable, idempotent upgrade of our own models only."""
    m = copy.deepcopy(model)
    changed = False
    if kind in ('image','images'):
        for key in ('qfmt','afmt'):
            cleaned = re.sub(r'<div>\s*<button\b[^>]*\bid=[\"\']toggle[\"\'][^>]*>.*?</button>\s*</div>', '', m['tmpls'][0][key], flags=re.S|re.I)
            if cleaned != m['tmpls'][0][key]:
                m['tmpls'][0][key] = cleaned; changed=True
    for field in (['Header','InlineData'] if kind=='cloze_input' else ['Header']):
        if field not in [f['name'] for f in m['flds']]:
            col.models.add_field(m,col.models.new_field(field)); changed=True
    if kind=='cloze_input':
        from .card_style import WRAP_MARK
        for key,side in [('qfmt','question'),('afmt','answer')]:
            fallback = '{{cloze:Back}}<br>{{type:cloze:Back}}'+('{{Extra}}' if side=='answer' else '')
            expected = '{{#InlineData}}'+inline_template(side)+'{{/InlineData}}{{^InlineData}}'+fallback+'{{/InlineData}}'+(HEADER_TEMPLATE if side=='answer' else '')
            wrapped = WRAP_MARK+'<div class="ns-card ns-card-cloze_input">'+expected+'</div>'
            if m['tmpls'][0][key] not in (expected,wrapped): m['tmpls'][0][key]=expected; changed=True
    elif HEADER_MARK not in m['tmpls'][0]['afmt']:
        m['tmpls'][0]['afmt'] += HEADER_TEMPLATE; changed=True
    for css,marker in [(HEADER_CSS,'.ns-header{'),(INLINE_CSS,'.ns-inline-input{')]:
        if marker not in m['css']:
            m['css'] += css; changed=True
    if HEADER_STYLE_MARK not in m['css']:
        m['css'] += HEADER_STYLE_MARK+HEADER_CSS; changed=True
    from .card_style import apply_style
    apply_style(m,kind)
    changed = m!=model
    if changed:
        col.models.update_dict(m)
        return col.models.get(m['id'])
    return model
