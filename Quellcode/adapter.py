"""Anki collection access; no network and no direct SQL writes."""
import json
import hashlib
import re
import base64
from collections import Counter
from .core import SyncError, ident, plan
from .deck_names import resolve, old_decks
from .type_models import get_model, change_model
from .mask_state import prepare as prepare_masks,review_record
from .card_extras import ensure_features,HEADER_MARK,legacy_header

TAG = 'notion_safe_sync_v1'
MODEL = 'Notion Safe Sync'


def snapshot(col, note_ids=None):
    result, unknown = {}, []
    ids = set(note_ids) if note_ids is not None else set(col.find_notes('tag:' + TAG)) | set(col.find_notes('note:Notion-Basic'))
    for nid in sorted(ids):
        n = col.get_note(nid)
        managed = TAG in n.tags
        try:
            meta = {}
            if managed:
                if 'NotionSync' in n:
                    encoded = n['NotionSync']
                    meta = json.loads(base64.b64decode(encoded[3:]).decode('utf-8') if encoded.startswith('v3:') else encoded)
                else:
                    encoded = next((t[5:] for t in n.tags if t.startswith('nss2_')),None)
                    meta = json.loads(bytes.fromhex(encoded).decode('utf-8')) if encoded else json.loads(next(t[4:] for t in n.tags if t.startswith('nss_')))
                bid, page = ident(meta['block']), ident(meta['page'])
            else:
                url = n['NotionID']
                if '#' not in url:
                    raise ValueError()
                root, fragment = url.split('#')
                bid, page = ident(fragment), ident(root)
            cards = n.cards()
            kind = meta.get('kind','basic')
            ids = meta.get('ids',[1])
            if len(n.note_type()['tmpls']) != 1 or not cards or len({c.ord for c in cards})!=len(cards) or set(c.ord+1 for c in cards)!=set(ids):
                raise ValueError()
            if bid in result:
                raise SyncError('Mehrdeutige Altkarten/Block-ID: ' + bid)
            image = re.search(r'<img src="([^"]+)"',n['Image']) if 'Image' in n else None
            result[bid] = dict(nid=nid, page=page, block=bid, front=n['Front'], back=n['Back'].split(HEADER_MARK,1)[0] if 'Header' not in n else n['Back'], deck=col.decks.name(cards[0].odid or cards[0].did), managed=managed, legacy=not managed, root=meta.get('root'), topics=meta.get('topics',[]),kind=kind,ids=ids,extra=n['Extra'] if 'Extra' in n else '',image=image[1] if image else '',masks=meta.get('masks',[]),mode=meta.get('mode',''),order=meta.get('order',[]),mask_hash=meta.get('mask_hash',''),cards={c.ord+1:c.id for c in cards},mixed_decks=len({c.odid or c.did for c in cards})>1,header=n['Header'] if 'Header' in n else meta.get('header',''),inline_data=n['InlineData'] if 'InlineData' in n else '',mask_review=meta.get('mask_review'))
        except SyncError:
            raise
        except Exception:
            unknown.append(nid)
    if unknown:
        raise SyncError('Migration ungeklärt. Notiz-IDs ohne eindeutige Herkunft/einzelne Karte: ' + ', '.join(map(str, unknown)) + '. Diese Notizen zuerst manuell zuordnen oder in einen anderen Notiztyp auslagern. Keine Änderungen ausgeführt.')
    return result


def model(col):
    m = col.models.by_name(MODEL)
    if m:
        if [f['name'] for f in m['flds']] not in (['Front','Back','NotionID','NotionSync'],['Front','Back','NotionID','NotionSync','Header']) or len(m['tmpls']) != 1:
            raise SyncError('Eigener Notiztyp wurde inkompatibel verändert.')
        return m
    m = col.models.new(MODEL)
    for name in ('Front','Back','NotionID','NotionSync'):
        col.models.add_field(m, col.models.new_field(name))
    t = col.models.new_template('Frage–Antwort')
    t['qfmt'] = '{{Front}}'
    t['afmt'] = '{{FrontSide}}<hr id="answer">{{Back}}'
    col.models.add_template(m, t)
    m['css'] = '.card {font-family:Arial;font-size:20px;text-align:left} img {max-width:100%} table,td {border:1px solid #999;border-collapse:collapse} figcaption {font-size:80%}'
    col.models.add(m)
    return m


def prepare_decks(col, desired, existing):
    resolve(desired,existing,[d.name for d in col.decks.all_names_and_ids()])


def migration_details(desired,existing):
    details = []
    for bid,value in desired.items():
        old = existing.get(bid)
        if not old: continue
        removed = sorted(set(old.get('ids',[1]))-set(value.get('ids',[1])))
        if old.get('kind','basic') != value.get('kind','basic') or removed:
            details.append(dict(block=bid,nid=old['nid'],old=old.get('kind','basic'),new=value.get('kind','basic'),removed=removed,card_ids=[old['cards'][i] for i in removed]))
    return details


def approval_keys(desired,existing):
    prepare_masks(desired,existing)
    keys = set()
    details = migration_details(desired,existing)
    if details:
        keys.add('migration:'+hashlib.sha256(json.dumps(details,sort_keys=True).encode()).hexdigest())
    for bid,value in desired.items():
        signature = value.get('mask_hash')
        if signature and existing.get(bid,{}).get('mask_hash') != signature:
            keys.add('mask:'+signature)
    return keys


def apply(col, desired, active, before, media, summary, approvals=()):
    current = snapshot(col)
    if current != before:
        raise SyncError('Sammlung seit Vorschau verändert. Bitte Vorschau erneut starten.')
    prepare_decks(col,desired,current)
    prepare_masks(desired,current)
    if not approval_keys(desired,current).issubset(set(approvals)):
        raise SyncError('Typwechsel, einzelne Kartenlöschungen oder neue/geänderte Bildmasken müssen zuerst ausdrücklich in der Vorschau bestätigt werden.')
    cleanup = old_decks(current,active,{v['root'] for v in desired.values() if v.get('root')})
    actions = plan(desired, current, active)
    # Media writes are append-only and intentionally outside collection undo.
    for name, data in media.items():
        actual = col.media.write_data(name, data)
        if actual != name:
            for value in desired.values():
                for field in ('front','back','extra','header'):
                    if field in value: value[field] = value[field].replace('src="' + name + '"', 'src="' + actual + '"')
                if value.get('image')==name: value['image'] = actual
    actions = plan(desired, current, active)
    undo = col.add_custom_undo_entry('Notion sicher synchronisieren')
    def checkpoint():
        # Keep our anchor alive: Anki's undo history has a bounded length.
        # A single final merge loses the anchor during larger imports.
        return col.merge_undo_entries(undo)
    try:
        models = {}
        upgraded = set()
        for bid,value in desired.items():
            if bid in current:
                old_model = col.get_note(current[bid]['nid']).note_type()
                if old_model['name'].startswith('Notion Safe Sync') and old_model['id'] not in upgraded:
                    ensure_features(col,old_model,current[bid].get('kind','basic'))
                    upgraded.add(old_model['id'])
                    checkpoint()
        for action,bid in actions:
            if action=='new' or (action=='update' and desired[bid].get('kind','basic')!=current[bid].get('kind','basic')):
                kind = desired[bid].get('kind','basic')
                if kind not in models:
                    models[kind] = model(col) if kind=='basic' else get_model(col,kind)
                    models[kind] = ensure_features(col,models[kind],kind)
                    checkpoint()
        checkpoint()
        for action, bid in actions:
            if action in ('delete', 'same') and (action != 'same' or current[bid]['managed']):
                continue
            v = desired[bid]
            old = current.get(bid)
            kind = v.get('kind','basic')
            n = col.get_note(old['nid']) if old else col.new_note(models[kind])
            if old and old.get('kind','basic')!=kind:
                target = models.get(kind) or (model(col) if kind=='basic' else get_model(col,kind))
                checkpoint()
                n = change_model(col,n,target,v)
                checkpoint()
            n['Front'], n['Back'] = v['front'], v['back']
            if 'Header' in n: n['Header'] = v.get('header','')
            else: n['Back'] += legacy_header(v.get('header',''))
            if 'InlineData' in n: n['InlineData'] = v.get('inline_data','')
            n['NotionID'] = 'https://www.notion.so/' + v['page'] + '#' + bid
            if 'Extra' in n: n['Extra'] = v.get('extra','')
            if 'Image' in n: n['Image'] = '<img src="'+v['image']+'">' if v.get('image') else ''
            meta_value = {'page':v['page'], 'block':bid, 'root':v.get('root'), 'topics':v.get('topics',[])}
            for key,default in [('kind','basic'),('ids',[1]),('masks',[]),('mode',''),('order',[]),('mask_hash','')]:
                meta_value[key] = v.get(key,default)
            meta_value['header'] = v.get('header','')
            if v.get('kind') in ('image','images','sequence'):
                meta_value['mask_review'] = review_record(v)
            meta = json.dumps(meta_value, separators=(',', ':'))
            n.tags = [t for t in n.tags if not t.startswith(('nss_','nss2_'))]
            if TAG not in n.tags:
                n.tags.append(TAG)
            if 'NotionSync' in n:
                n['NotionSync'] = 'v3:'+base64.b64encode(meta.encode('utf-8')).decode('ascii')
            else:
                # Preserve legacy model and card IDs; provenance travels with note.
                n.tags.append('nss2_' + meta.encode('utf-8').hex())
            did = col.decks.id(v['deck'])
            checkpoint()
            if old:
                col.update_note(n)
                checkpoint()
                cards = n.cards()
                obsolete = [c.id for c in cards if c.ord+1 not in v.get('ids',[1])]
                if obsolete:
                    col.remove_cards_and_orphaned_notes(obsolete)
                    checkpoint()
                    cards = n.cards()
                if any(c.odid for c in cards):
                    raise SyncError('Karte liegt in einem Filterstapel. Zuerst Filterstapel leeren.')
                if any(c.did != did for c in cards):
                    col.set_deck([c.id for c in cards], did)
                    checkpoint()
            else:
                col.add_note(n, did)
                checkpoint()
            if set(c.ord+1 for c in n.cards()) != set(v.get('ids',[1])):
                raise SyncError('Anki erzeugte nicht die erwarteten Karten-IDs. Anwendung wird zurückgenommen.')
        deletes = [current[bid]['nid'] for action, bid in actions if action == 'delete']
        if deletes:
            col.remove_notes(deletes)
            checkpoint()
        for name in sorted(cleanup,key=lambda n:n.count('::'),reverse=True):
            # Never remove a deck with cards (including foreign ones) or children.
            decks = col.decks.all_names_and_ids()
            did = col.decks.id_for_name(name)
            if did and not any(d.name.casefold().startswith(name.casefold()+'::') for d in decks):
                query = 'deck:"' + name.replace('\\','\\\\').replace('"','\\"') + '"'
                if not col.find_cards(query):
                    col.decks.remove([did])
                    checkpoint()
        changes = checkpoint()
        summary.update(Counter(a for a, _ in actions))
        return changes
    except Exception as application_error:
        # All collection changes use undoable APIs; never proceed to deletion on failure.
        try:
            changes = col.merge_undo_entries(undo)
            if col.op_made_changes(changes):
                col.undo()
        except Exception as rollback_error:
            failure = SyncError('Anwendung und automatische Rücknahme fehlgeschlagen. Teiländerungen sind möglich. Keinen weiteren Sync starten. Sammlung zuerst sichern und den Zustand prüfen; eine Wiederherstellung ist nicht automatisch erforderlich.')
            failure.application_error = application_error
            failure.rollback_error = rollback_error
            raise failure from None
        raise
