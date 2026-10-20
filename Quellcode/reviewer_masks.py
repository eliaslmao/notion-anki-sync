"""Targeted Desktop Reviewer bridge; no edit controls in mobile/preview HTML."""
import secrets
import json
from aqt import gui_hooks
from aqt.reviewer import Reviewer
from aqt.qt import QTimer
from .adapter import TAG
from .card_types import IMAGE_TYPES

_active = None
_installed = False


def render(text,card,context):
    global _active
    from . import ui
    mw = ui.mw
    if context not in ('reviewQuestion','reviewAnswer') or not mw or mw.state!='review' or not isinstance(mw.reviewer,Reviewer) or not mw.reviewer.card or mw.reviewer.card.id!=card.id:
        return text
    from .reviewer_interactions import restore_fullscreen
    restore_fullscreen()
    try:
        from .adapter import snapshot
        note = card.note()
        if TAG not in note.tags: return text
        value = next(iter(snapshot(mw.col,[note.id]).values()))
        from .card_style import CARD_CSS,WRAP_MARK,INTERACTION_SCRIPT
        # Managed legacy notes may share an old model with unrelated notes.
        # Style only their current Desktop display, never the shared model.
        if WRAP_MARK not in text:
            text = '<style>'+CARD_CSS+'</style>'+WRAP_MARK+'<div class="ns-card">'+text+INTERACTION_SCRIPT+'</div>'
    except Exception: return text
    token = secrets.token_hex(16)
    _active = (mw.reviewer,card.id,token)
    zoom = {action:'nss-zoom-'+action+':'+str(card.id)+':'+token for action in ('open','close')}
    text += '<script>window.nsImageBridge='+json.dumps(zoom)+';</script>'
    if value['kind'] not in IMAGE_TYPES: return text
    command = 'nss-mask-edit:'+str(card.id)+':'+token
    return text+'<div class="ns-local-actions"><button type="button" id="ns-mask-edit" onclick="event.preventDefault();event.stopPropagation();pycmd(\''+command+'\');">Masken bearbeiten</button></div>'


def bridge(handled,message,context):
    if not message.startswith(('nss-mask-edit:','nss-zoom-open:','nss-zoom-close:')): return handled
    if handled[0]: return handled
    from . import ui
    mw = ui.mw
    if not _active or not isinstance(context,Reviewer): return True,None
    reviewer,cid,token = _active
    action=message.split(':',1)[0]
    if context is not reviewer or not mw or mw.reviewer is not reviewer or mw.state!='review' or not reviewer.card or reviewer.card.id!=cid or message!=action+':'+str(cid)+':'+token:
        return True,None
    if action.startswith('nss-zoom-'):
        from .reviewer_interactions import open_fullscreen,restore_fullscreen
        if action=='nss-zoom-open': open_fullscreen(reviewer)
        else: restore_fullscreen()
        return True,None
    nid = reviewer.card.nid
    from .adapter import snapshot
    try:
        value = next(iter(snapshot(mw.col,[nid]).values()))
        selected = reviewer.card.ord+1 if value['kind'] in ('image','images') else None
        from .local_mask_ui import start
        QTimer.singleShot(0,lambda:start(nid,selected,reviewer))
    except Exception as error: ui.finish_error(error)
    return True,None


def install():
    global _installed
    if _installed: return
    from .reviewer_interactions import install as install_interactions
    install_interactions()
    gui_hooks.card_will_show.append(render)
    gui_hooks.webview_did_receive_js_message.append(bridge)
    _installed = True
