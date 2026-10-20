"""Per-note source/effective geometry and persistent local corrections."""
import copy
import hashlib
import json
import math
from .core import SyncError
from .card_types import image_clozes,sequence_html,IMAGE_TYPES


def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def prepare(desired,existing):
    for bid,value in desired.items():
        if value.get('kind') not in IMAGE_TYPES: continue
        if '_source_masks' not in value:
            value['_source_masks'] = copy.deepcopy(value['masks'])
            value['_source_order'] = list(value.get('order',[]))
            value['source_signature'] = digest(dict(block=bid,kind=value['kind'],image=value.get('image_hash',value['image']),masks=value['_source_masks'],mode=value.get('mode',''),order=value['_source_order']))
            value['review_source_signature'] = digest(dict(source=value['source_signature'],front=value['front'],header=value.get('header',''),extra=value.get('extra','')))
        old = existing.get(bid,{}).get('mask_review') or {}
        if old and old.get('source_signature') == value['source_signature'] and old.get('block')==bid and old.get('kind')==value['kind']:
            value['_mask_conflict'] = False
            if not value.get('_editor_confirmed'):
                value['masks'] = copy.deepcopy(old['masks'])
                value['order'] = list(old.get('order',[]))
            value['_review_required'] = old.get('review_source_signature')!=value['review_source_signature']
        else:
            value['_review_required'] = True
            value['_mask_conflict'] = bool(old and old.get('edited'))
        rebuild(value,bid)


def rebuild(value,bid=None):
    bid = bid or value['block']
    masks = value['masks']
    for items in (masks,value.get('_source_masks',masks)):
        if not isinstance(items,list) or any(not isinstance(m,dict) or type(m.get('id')) is not int or not 1<=m['id']<=499 for m in items):
            raise SyncError('Unlesbare Maskendaten: stabile Abdeckungs-IDs 1–499 erforderlich.')
    allowed = {m['id'] for m in value.get('_source_masks',masks)}
    ids = [m['id'] for m in masks]
    if not masks or len(set(ids))!=len(ids) or not set(ids).issubset(allowed):
        raise SyncError('Mindestens eine Abdeckung muss erhalten bleiben. IDs dürfen nicht geändert oder neu vergeben werden.')
    if value['kind']=='image' and len(masks)!=1: raise SyncError('Bildlücke benötigt eine Abdeckung.')
    for m in masks:
        x,y,w,h = [m[k] for k in ('x','y','w','h')]
        if not all(isinstance(n,(float,int)) and math.isfinite(n) for n in (x,y,w,h)) or not (0<=x<100 and 0<=y<100 and w>0 and h>0 and x+w<=100.000001 and y+h<=100.000001):
            raise SyncError('Abdeckung liegt außerhalb des Originalbildes oder hat keine positive Fläche.')
    value['masks'].sort(key=lambda m:m['id'])
    if value['kind']=='sequence':
        value['order'] = [i for i in value.get('_source_order',value['order']) if i in ids]
        value['ids'] = [1]
        value['back'] = sequence_html(value)
    else:
        value['ids'] = sorted(ids)
        value['back'] = image_clozes(value)
    value['mask_hash'] = digest(dict(block=bid,kind=value['kind'],source=value['source_signature'],review=value['review_source_signature'],masks=value['masks'],order=value['order']))


def review_record(value):
    return dict(block=value['block'],kind=value['kind'],image_hash=value.get('image_hash'),source_signature=value['source_signature'],review_source_signature=value['review_source_signature'],source_masks=copy.deepcopy(value['_source_masks']),source_order=list(value.get('_source_order',[])),source_mode=value.get('mode',''),masks=copy.deepcopy(value['masks']),order=list(value.get('order',[])),edited=value['masks']!=value['_source_masks'] or value.get('order',[])!=value.get('_source_order',[]))
