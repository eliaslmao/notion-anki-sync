"""Typed leaf parsing and deterministic payloads; no Anki/account required."""
import hashlib
import html
import json
import re
from .core import SyncError, rich, usable

TYPES = {'Eingabe':'input','Lücke':'cloze','Lücke+Eingabe':'cloze_input',
         'Bildlücke':'image','Bildlücken':'images','Bildfolge':'sequence'}
IMAGE_TYPES = {'image','images','sequence'}


def plain(items):
    return ''.join(x.get('plain_text',x.get('text',{}).get('content','')) for x in items)


def title_type(items):
    text = plain(items).lstrip()
    match = re.match(r'^\[([^\]]+)\]',text)
    if not match:
        if text.startswith('['): raise SyncError('Unvollständiger Typmarker im Toggle-Titel.')
        return 'basic',rich(items)
    if match[1] not in TYPES:
        raise SyncError('Unbekannter Kartentypmarker. Unterstützt: Eingabe, Lücke, Lücke+Eingabe, Bildlücke, Bildlücken, Bildfolge.')
    # Remove just the marker while preserving annotations on remaining text.
    count = len(plain(items))-len(text)+match.end()
    remaining = []
    for item in items:
        length = len(plain([item]))
        if count >= length:
            count -= length
            continue
        value = json.loads(json.dumps(item))
        if count:
            if value.get('type') != 'text': raise SyncError('Typmarker muss normaler Text sein.')
            value['text']['content'] = value['text']['content'][count:]
            value.pop('plain_text',None)
            count = 0
        remaining.append(value)
    return TYPES[match[1]],rich(remaining).lstrip()


def cloze_ids(text):
    """Validate balanced (also nested) native clozes, keeping numeric identity."""
    stack, ids, index = [], set(), 0
    while index < len(text):
        if text.startswith('{{',index):
            m = re.match(r'\{\{c([1-9]\d*)::',text[index:])
            if not m or int(m[1]) > 499:
                raise SyncError('Ungültige Cloze-Syntax. Erwartet: {{c1::Text}}; IDs 1–499.')
            stack.append((int(m[1]), index+len(m[0])))
            ids.add(int(m[1]))
            index += len(m[0])
        elif text.startswith('}}',index):
            if not stack: raise SyncError('Cloze-Klammern sind nicht ausgeglichen.')
            _, start = stack.pop()
            if not text[start:index].split('::',1)[0].strip(): raise SyncError('Leere Cloze-Antwort.')
            index += 2
        else:
            index += 1
    if stack or not ids: raise SyncError('Fehlende oder unvollständige Cloze-Syntax.')
    return sorted(ids)


def split_extra(children):
    main, extra, started = [], [], False
    for b in children:
        if b['type'] == 'paragraph':
            text = plain(b['paragraph'].get('rich_text',[])).strip()
            if text.startswith('Zusatzinfo:'):
                if started: raise SyncError('Zusatzinfo: darf nur einmal vorkommen.')
                started = True
                remainder = text[len('Zusatzinfo:'):].strip()
                if remainder:
                    value = json.loads(json.dumps(b))
                    value['paragraph']['rich_text'] = [{'type':'text','text':{'content':remainder}}]
                    extra.append(value)
                extra.extend(b.get('_children',[]))
                continue
        (extra if started else main).append(b)
    return main,extra


def parse_typed(kind, title, children, renderer):
    from .card_extras import inert_braces
    main,extra_blocks = split_extra(children)
    extra = inert_braces(''.join(renderer.block(b) for b in extra_blocks))
    result = dict(kind=kind,front=inert_braces(title),extra=extra,ids=[1],masks=[],image='',mode='',order=[])
    if kind == 'input':
        parts = []
        for b in main:
            if b['type'] != 'paragraph' or b.get('_children'):
                raise SyncError('[Eingabe] erwartet genau eine kurze einzeilige Textantwort vor Zusatzinfo:.')
            text = plain(b['paragraph'].get('rich_text',[])).strip()
            if text: parts.append(text)
        if len(parts)!=1 or '\n' in parts[0] or '\r' in parts[0] or len(parts[0])>500 or not usable(title):
            raise SyncError('[Eingabe]: Frage und genau eine einzeilige Antwort sind erforderlich (max. 500 Zeichen).')
        result['back'] = html.escape(parts[0])
    elif kind in ('cloze','cloze_input'):
        content = ''.join(renderer.block(b) for b in main)
        result['ids'] = cloze_ids(html.unescape(re.sub('<[^>]*>','',content)))
        # Retain the organizational title in the note/browser; native templates
        # intentionally display only the cloze body as the question.
        result['back'] = content
        if kind=='cloze_input':
            from .card_extras import inline_payload
            result['back'],result['inline_data'] = inline_payload(content)
    else:
        images = [b for b in main if b['type']=='image']
        if len(images)!=1 or not usable(title): raise SyncError('Bildtyp benötigt eine Aufgabenstellung und genau ein direktes Originalbild.')
        rendered = renderer.block(images[0])
        result['image'] = re.search(r'<img src="([^"]+)"',rendered)[1]
        result['image_hash'] = hashlib.sha256(renderer.media[result['image']]).hexdigest()
        controls = []
        for b in main:
            if b['type']=='image': continue
            if b['type']!='paragraph' or b.get('_children'):
                raise SyncError('Bild-Steuerdaten müssen normale Textabsätze sein.')
            controls.append(plain(b['paragraph'].get('rich_text',[])))
        text = '\n'.join(controls)
        pattern = r'Abdeckung\s+([1-9]\d*)\s*:\s*x\s*=\s*([\d.]+)%\s*,\s*y\s*=\s*([\d.]+)%\s*,\s*breite\s*=\s*([\d.]+)%\s*,\s*höhe\s*=\s*([\d.]+)%'
        seen = set()
        def mask(match):
            mid = int(match[1])
            if mid in seen or mid>499: raise SyncError('Doppelte/ungültige Abdeckungs-ID (erlaubt: 1–499).')
            seen.add(mid)
            try: x,y,w,h = [float(match[i]) for i in range(2,6)]
            except ValueError: raise SyncError('Ungültige Koordinaten.') from None
            if not (0<=x<100 and 0<=y<100 and w>0 and h>0 and x+w<=100 and y+h<=100):
                raise SyncError('Abdeckung liegt außerhalb des Originalbildes oder hat keine positive Fläche.')
            result['masks'].append(dict(id=mid,x=x,y=y,w=w,h=h))
            return ''
        text = re.sub(pattern,mask,text)
        modes = re.findall(r'Modus:\s*([^\n]+)',text)
        orders = re.findall(r'Reihenfolge:\s*([^\n]+)',text)
        text = re.sub(r'(?:Modus|Reihenfolge):[^\n]*','',text)
        if text.strip() or not seen: raise SyncError('Unbekannte/unvollständige Bild-Steuerdaten oder fehlende Abdeckung.')
        if len(modes)>1 or len(orders)>1: raise SyncError('Modus/Reihenfolge mehrfach angegeben.')
        if kind=='image' and len(seen)!=1: raise SyncError('[Bildlücke] benötigt genau eine Abdeckung.')
        if kind in ('images','sequence') and len(seen)<2: raise SyncError('Mehrfach-Bildtyp benötigt mindestens zwei Abdeckungen.')
        if kind=='images':
            if modes not in (['Alle verdecken, eine abfragen'],['Eine verdecken, eine abfragen']) or orders:
                raise SyncError('[Bildlücken] benötigt genau einen unterstützten Modus und keine Reihenfolge.')
            result['mode'] = 'all' if modes[0].startswith('Alle') else 'one'
        elif modes: raise SyncError('Modus ist nur bei [Bildlücken] erlaubt.')
        if kind=='sequence':
            if len(orders)!=1 or not re.fullmatch(r'\s*\d+(?:\s*,\s*\d+)*\s*',orders[0]):
                raise SyncError('[Bildfolge] benötigt Reihenfolge: 1, 2 mit allen Abdeckungs-IDs.')
            result['order'] = [int(x.strip()) for x in orders[0].split(',')]
            if len(result['order'])!=len(seen) or set(result['order'])!=seen: raise SyncError('Reihenfolge muss jede Abdeckungs-ID genau einmal enthalten.')
        elif orders: raise SyncError('Reihenfolge ist nur bei [Bildfolge] erlaubt.')
        result['masks'].sort(key=lambda m:m['id'])
        result['ids'] = [1] if kind=='sequence' else sorted(seen)
        result['back'] = image_clozes(result) if kind!='sequence' else sequence_html(result)
        result['mask_hash'] = hashlib.sha256(json.dumps({k:result[k] for k in ('image','masks','mode','order')},sort_keys=True).encode()).hexdigest()
    return result


def image_clozes(value):
    inactive = 0 if value.get('mode')=='one' else 1
    return '<br>'.join('{{c%d::image-occlusion:rect:left=%g:top=%g:width=%g:height=%g:oi=%d}}' % (m['id'],m['x']/100,m['y']/100,m['w']/100,m['h']/100,inactive) for m in value['masks'])


def sequence_html(value, preview=False):
    masks = ''.join('<button type="button" class="ns-mask" data-mask="%d" style="left:%g%%;top:%g%%;width:%g%%;height:%g%%">%d</button>' % (m['id'],m['x'],m['y'],m['w'],m['h'],m['id']) for m in value['masks'])
    order = html.escape(json.dumps(value.get('order') or [m['id'] for m in value['masks']]),quote=True)
    return '<div class="ns-widget" data-order="'+order+'"><div class="ns-picture"><img src="'+html.escape(value['image'],quote=True)+'">'+masks+'</div><br><button type="button" class="ns-next">Nächste Abdeckung aufdecken</button><button type="button" class="ns-reset">Zurücksetzen</button></div>'


SEQUENCE_CSS = '.ns-picture{position:relative;display:inline-block;max-width:100%;line-height:0}.ns-picture img{display:block;max-width:100%;height:auto}.ns-mask{position:absolute;margin:0;border:2px solid #973600;border-radius:0;background:#ffd46a;color:#191919;box-sizing:border-box;cursor:pointer;line-height:normal;padding:0}.ns-answer .ns-mask{visibility:hidden}.ns-answer .ns-next,.ns-answer .ns-reset{display:none}'
SEQUENCE_JS = '''<script>(function(){document.querySelectorAll('.ns-widget').forEach(function(w){var order=JSON.parse(w.dataset.order),i=0;function reveal(id){var m=w.querySelector('[data-mask="'+id+'"]');if(m)m.style.visibility='hidden'}w.querySelector('.ns-next').onclick=function(e){e.preventDefault();if(i<order.length)reveal(order[i++]);this.disabled=i>=order.length};w.querySelector('.ns-reset').onclick=function(e){e.preventDefault();i=0;w.querySelectorAll('.ns-mask').forEach(function(m){m.style.visibility='visible'});w.querySelector('.ns-next').disabled=false};if(w.dataset.preview==='1')w.querySelectorAll('.ns-mask').forEach(function(m){m.onclick=function(e){e.preventDefault();m.style.visibility='hidden'}})})})();</script>'''
