"""Offline mask drafts and atomic, undoable writes shared by both UI entries."""
import base64
import copy
import hashlib
import json
from pathlib import Path
from .core import SyncError
from .adapter import snapshot, TAG, migration_details
from .card_types import IMAGE_TYPES
from .mask_state import prepare, rebuild, review_record, digest


def read_local(col, nid):
    try:
        before = snapshot(col, [nid])
        value = copy.deepcopy(next(iter(before.values())))
        if not value['managed'] or value['kind'] not in IMAGE_TYPES:
            raise ValueError()
        note = col.get_note(nid)
        if 'NotionID' not in note or not note['NotionID'].endswith('#'+value['block']): raise ValueError()
        matches = col.find_notes('tag:'+TAG+' NotionID:*'+value['block'])
        if set(matches)!={nid}:
            raise SyncError('Bildnotiz '+str(nid)+': Mehrdeutige Quellidentität. Doppelte Notion-Notizen zuerst zuordnen. Keine Änderungen gespeichert.')
        if value['mixed_decks'] or any(c.odid for c in col.get_note(nid).cards()):
            raise SyncError('Bildnotiz '+str(nid)+': Karten liegen in verschiedenen Stapeln oder einem Filterstapel. Zuerst eindeutig zuordnen / Filterstapel leeren.')
        name = value['image']
        if not name or Path(name).name != name or '/' in name or '\\' in name or ':' in name:
            raise SyncError('Bildnotiz '+str(nid)+': Kein sicher zuordenbares lokales Originalbild.')
        path = Path(col.media.dir()) / name
        try: image = path.read_bytes()
        except OSError:
            raise SyncError('Bildnotiz '+str(nid)+': Das Originalbild fehlt in Ankis Mediensammlung oder kann nicht gelesen werden.') from None
        image_hash = hashlib.sha256(image).hexdigest()
        old = value.get('mask_review')
        value['image_hash'] = image_hash
        if value['kind']=='images' and value['mode'] not in ('all','one'):
            raise ValueError()
        if value['kind']!='images' and value['mode']:
            raise ValueError()
        if old:
            if old['block']!=value['block'] or old['kind']!=value['kind'] or old['image_hash']!=image_hash or old['masks']!=value['masks'] or old['order']!=value['order'] or old['source_mode']!=value['mode']:
                raise ValueError()
            value['_source_masks'] = copy.deepcopy(old['source_masks'])
            value['_source_order'] = list(old['source_order'])
            if value['kind']=='sequence':
                source_ids = [m['id'] for m in value['_source_masks']]
                if len(value['_source_order'])!=len(source_ids) or set(value['_source_order'])!=set(source_ids): raise ValueError()
            elif value['_source_order'] or value['order']: raise ValueError()
            value['source_signature'] = old['source_signature']
            value['review_source_signature'] = old['review_source_signature']
            expected = digest(dict(block=value['block'],kind=value['kind'],image=image_hash,masks=value['_source_masks'],mode=value['mode'],order=value['_source_order']))
            if expected!=value['source_signature']: raise ValueError()
            rebuild(value)
            if value['mask_hash']!=before[value['block']]['mask_hash']: raise ValueError()
        else:
            # A pre-1.3 note can establish source provenance from its stored
            # image and geometry; the next fetch still detects source changes.
            prepare({value['block']:value},{})
        if value['back']!=before[value['block']]['back'] or value['ids']!=before[value['block']]['ids']:
            raise ValueError()
        value['_editor_confirmed'] = True
        return before, value, image
    except SyncError:
        raise
    except Exception:
        raise SyncError('Bildnotiz '+str(nid)+': Maskendaten oder Kartenidentität sind nicht eindeutig lesbar. Keine Änderung gespeichert.') from None


def candidates(col):
    values, errors = {}, []
    ambiguous = set()
    for nid in col.find_notes('tag:'+TAG):
        n = col.get_note(nid)
        # Non-image notes need not have any mask data.
        if 'Image' not in n: continue
        try:
            state = next(iter(snapshot(col,[nid]).values()))
            if state['kind'] not in IMAGE_TYPES: continue
            before, value, _ = read_local(col,nid)
            if value['block'] in values or value['block'] in ambiguous:
                values.pop(value['block'],None)
                ambiguous.add(value['block'])
                raise SyncError('Mehrdeutige Block-ID bei lokalen Bildnotizen. Bitte Herkunft zuerst klären.')
            values[value['block']] = (before,value)
        except SyncError as error: errors.append(str(error))
    return values, errors


def changed(before, drafts):
    return {bid:v for bid,v in drafts.items() if v['masks']!=before[bid]['masks'] or v['order']!=before[bid]['order']}


def deletion_details(before,drafts):
    return migration_details(drafts,before)


def save(col, before, drafts, approved_deletions=()):
    drafts = copy.deepcopy(drafts)
    # No writes (including undo/model updates) for an unchanged save.
    drafts = changed(before,drafts)
    if not drafts: return None
    for bid,value in drafts.items():
        current, original, _ = read_local(col,before[bid]['nid'])
        if current[bid]!=before[bid]:
            raise SyncError('Bildnotiz seit der Vorschau verändert. Bitte erneut öffnen. Keine Änderungen gespeichert.')
        # The editor may change geometry/removal only. Never accept altered
        # source identity, image, type, title, deck or arbitrary field content.
        safe = copy.deepcopy(original)
        safe['masks'] = copy.deepcopy(value['masks'])
        rebuild(safe)
        drafts[bid] = safe
    details = deletion_details(before,drafts)
    removed = {cid for d in details for cid in d['card_ids']}
    if removed != set(approved_deletions):
        raise SyncError('Einzelkartenlöschung muss mit den betroffenen Karten ausdrücklich bestätigt werden.')
    undo = col.add_custom_undo_entry('Lokale Bildmasken bearbeiten')
    def checkpoint(): return col.merge_undo_entries(undo)
    try:
        for bid,value in drafts.items():
            n = col.get_note(before[bid]['nid'])
            if 'NotionSync' not in n:
                raise SyncError('Bildnotiz hat kein unterstütztes Herkunftsfeld. Keine Änderungen gespeichert.')
            encoded = n['NotionSync']
            meta = json.loads(base64.b64decode(encoded[3:]).decode() if encoded.startswith('v3:') else encoded)
            for key in ('masks','ids','order','mask_hash'): meta[key] = value[key]
            meta['mask_review'] = review_record(value)
            n['Back'] = value['back']
            n['NotionSync'] = 'v3:'+base64.b64encode(json.dumps(meta,separators=(',',':')).encode()).decode()
            col.update_note(n); checkpoint()
            obsolete = [c.id for c in n.cards() if c.ord+1 not in value['ids']]
            if set(obsolete) != {before[bid]['cards'][i] for i in set(before[bid]['ids'])-set(value['ids'])}:
                raise SyncError('Karten nach Bearbeitung nicht eindeutig zuordenbar. Änderungen werden zurückgenommen.')
            if obsolete: col.remove_cards_and_orphaned_notes(obsolete); checkpoint()
            actual = {c.ord+1:c.id for c in n.cards()}
            expected = {i:cid for i,cid in before[bid]['cards'].items() if i in value['ids']}
            if actual!=expected: raise SyncError('Kartenidentität unerwartet geändert. Änderungen werden zurückgenommen.')
        return checkpoint()
    except Exception as error:
        try:
            changes = checkpoint()
            if col.op_made_changes(changes): col.undo()
        except Exception as rollback:
            failure = SyncError('Speichern und automatische Rücknahme fehlgeschlagen. Teiländerungen sind möglich. Sammlung sichern und prüfen.')
            failure.application_error, failure.rollback_error = error, rollback
            raise failure from None
        raise
