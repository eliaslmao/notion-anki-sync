"""Native Anki Cloze/typing/IO models; custom template only for image sequence."""
from .core import SyncError
from .card_types import SEQUENCE_CSS, SEQUENCE_JS

NAMES = {'input':'Notion Safe Sync – Eingabe','cloze':'Notion Safe Sync – Lücke',
         'cloze_input':'Notion Safe Sync – Lücke Eingabe','image':'Notion Safe Sync – Bildlücke',
         'images':'Notion Safe Sync – Bildlücken','sequence':'Notion Safe Sync – Bildfolge'}


def get_model(col,kind):
    name = NAMES[kind]
    existing = col.models.by_name(name)
    if existing:
        if not all(x in [f['name'] for f in existing['flds']] for x in ('Front','Back','NotionID','NotionSync','Extra','Image')) or len(existing['tmpls'])!=1:
            raise SyncError('Verwalteter Notiztyp wurde inkompatibel verändert.')
        return existing
    if kind in ('image','images'):
        from anki.stdmodels import get_stock_notetypes
        # Runtime-provided stock model: keep native IO field tags, JS and CSS.
        m = get_stock_notetypes(col)[5][1](col)
        renames = {m['flds'][i]['name']:v for i,v in enumerate(('Back','Image','Front','Extra','Comments'))}
        for f in m['flds']: f['name'] = renames[f['name']]
        for t in m['tmpls']:
            for key in ('qfmt','afmt'):
                for old,new in renames.items():
                    # Match references, not plain localized text/JavaScript.
                    import re
                    t[key] = re.sub(r'(\{\{(?:[#/^]|cloze:)?)(%s)(\}\})'%re.escape(old),lambda match:match[1]+new+match[3],t[key])
        for field in ('NotionID','NotionSync'):
            col.models.add_field(m,col.models.new_field(field))
    else:
        m = col.models.new(name)
        for f in ('Front','Back','NotionID','NotionSync','Extra','Image'):
            col.models.add_field(m,col.models.new_field(f))
        if kind in ('cloze','cloze_input'): m['type'] = 1
        t = col.models.new_template('Notion Card')
        if kind=='input':
            t['qfmt'] = '{{Front}}<br>{{type:Back}}'
            t['afmt'] = '{{Front}}<hr id="answer">{{type:Back}}<br>{{Extra}}'
        elif kind in ('cloze','cloze_input'):
            typing = '<br>{{type:cloze:Back}}' if kind=='cloze_input' else ''
            t['qfmt'] = '{{cloze:Back}}'+typing
            t['afmt'] = '{{cloze:Back}}'+typing+'<br>{{Extra}}'
        else:
            t['qfmt'] = '{{Front}}<br>{{Back}}'+SEQUENCE_JS
            t['afmt'] = '{{Front}}<br><div class="ns-answer">{{Back}}</div>{{Extra}}'+SEQUENCE_JS
        col.models.add_template(m,t)
        m['css'] = '.card{font:20px Arial;text-align:left}.cloze{font-weight:bold;color:#1670ca}img{max-width:100%}'+SEQUENCE_CSS
    m['name'] = name
    col.models.add(m)
    return m


def change_model(col,note,new_model,value):
    old = note.note_type()
    old_cloze = old['type']==1
    new_cloze = new_model['type']==1
    old_ids = [card.ord+1 for card in note.cards()]
    new_ids = value.get('ids',[1])
    # Single basic card can map unambiguously only to native ordinal 0.
    if old_cloze != new_cloze and (old_ids != [1] or 1 not in new_ids):
        raise SyncError('Nicht eindeutig zuordenbarer Typwechsel. Einzelkarte ↔ Cloze ist nur mit vorhandener ID 1 sicher möglich. Bitte Typwechsel separat manuell zuordnen.')
    info = col.models.change_notetype_info(old_notetype_id=old['id'],new_notetype_id=new_model['id'])
    request = info.input
    request.note_ids.append(note.id)
    old_fields = {f['name']:i for i,f in enumerate(old['flds'])}
    del request.new_fields[:]
    request.new_fields.extend(old_fields.get(f['name'],-1) for f in new_model['flds'])
    col.models.change_notetype_of_notes(request)
    return col.get_note(note.id)
