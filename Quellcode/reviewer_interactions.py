"""Desktop answer gate and reversible full-screen image presentation."""
from aqt.qt import QObject,QEvent,Qt,QApplication
from aqt.reviewer import Reviewer
from aqt import gui_hooks
from anki.hooks import wrap

_installed=False
_zoom=None
_filter=None


def restore_fullscreen(*_):
    global _zoom
    if _zoom is None: return
    _zoom=None


def open_fullscreen(reviewer):
    global _zoom
    if _zoom is not None: return
    mw=reviewer.mw
    # The enlarged image stays inside the resizable Anki window.
    # Keep the native window state and all Anki controls visible.
    _zoom=(mw,mw.windowState(),[])


def is_sequence(reviewer,question_only=True):
    if reviewer.mw.state!='review' or (question_only and reviewer.state!='question') or not reviewer.card: return False
    try:
        from .adapter import snapshot,TAG
        note=reviewer.card.note()
        return TAG in note.tags and next(iter(snapshot(reviewer.mw.col,[note.id]).values()))['kind']=='sequence'
    except Exception: return False


def answer_gate(reviewer,_old):
    if not is_sequence(reviewer): return _old(reviewer)
    if getattr(reviewer,'_ns_sequence_pending',False): return
    reviewer._clear_auto_advance_timers()
    reviewer._ns_sequence_pending=True
    cid=reviewer.card.id
    generation=getattr(reviewer,'_ns_sequence_generation',0)
    def checked(result):
        if generation!=getattr(reviewer,'_ns_sequence_generation',0): return
        reviewer._ns_sequence_pending=False
        if not reviewer.card or reviewer.card.id!=cid or reviewer.mw.state!='review' or reviewer.state!='question': return
        if result in ('complete','last'): _old(reviewer)
        elif result=='step':
            answer_button(reviewer,'Weiter aufdecken')
        else:
            from aqt.utils import tooltip
            tooltip('Bildreihenfolge noch nicht bereit. Bitte die Karte erneut öffnen.',parent=reviewer.mw)
    reviewer.web.evalWithCallback("(function(){var s=window.nsSequence;if(!s||!s.ready())return 'missing';if(s.remaining()>0){s.step(false);return s.remaining()?'step':'last'}return 'complete'})()",checked)


def answer_button(reviewer,text):
    import json
    reviewer.bottom.web.eval("(function(){var b=document.getElementById('ansbut');if(b&&b.firstChild)b.firstChild.textContent="+json.dumps(text+' ')+"})()")


def question_shown(card):
    from . import ui
    reviewer=ui.mw.reviewer
    reviewer._ns_sequence_pending=False
    reviewer._ns_sequence_generation=getattr(reviewer,'_ns_sequence_generation',0)+1
    if is_sequence(reviewer): answer_button(reviewer,'Weiter aufdecken')


def auto_question(reviewer,_old):
    if is_sequence(reviewer): reviewer._clear_auto_advance_timers(); return
    return _old(reviewer)


class InteractionFilter(QObject):
    def eventFilter(self,obj,event):
        if event.type() in (QEvent.Type.ShortcutOverride,QEvent.Type.KeyPress) and event.key() in (Qt.Key.Key_Space,Qt.Key.Key_Return,Qt.Key.Key_Enter) and event.isAutoRepeat() and QApplication.activeModalWidget() is None:
            from . import ui
            reviewer=getattr(ui.mw,'reviewer',None)
            if reviewer and is_sequence(reviewer,question_only=False):
                event.accept(); return True
        if _zoom is not None and QApplication.activeModalWidget() is None and event.type() in (QEvent.Type.ShortcutOverride,QEvent.Type.KeyPress) and event.key()==Qt.Key.Key_Escape:
            event.accept()
            if event.type()==QEvent.Type.KeyPress:
                mw=_zoom[0]
                mw.web.eval('if(window.nsCloseZoom)window.nsCloseZoom();')
                restore_fullscreen()
            return True
        return False


def install():
    global _installed,_filter
    if _installed: return
    Reviewer._showAnswer=wrap(Reviewer._showAnswer,answer_gate,'around')
    Reviewer._auto_advance_to_answer_if_enabled=wrap(Reviewer._auto_advance_to_answer_if_enabled,auto_question,'around')
    gui_hooks.reviewer_did_show_question.append(question_shown)
    gui_hooks.state_will_change.append(restore_fullscreen)
    gui_hooks.profile_will_close.append(restore_fullscreen)
    _filter=InteractionFilter(QApplication.instance())
    QApplication.instance().installEventFilter(_filter)
    _installed=True
