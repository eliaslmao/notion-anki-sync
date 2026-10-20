"""One explicit, transactional editor per changed Notion note."""
import copy
from aqt.qt import QDialog
from .mask_state import prepare
from .mask_editor import MaskEditor


def confirm(parent,desired,before,media,force=False):
    draft = copy.deepcopy(desired)
    prepare(draft,before)
    for bid,value in draft.items():
        if not value.get('_review_required') and not (force and value.get('kind') in ('image','images','sequence')):
            continue
        editor = MaskEditor(parent,value,media[value['image']])
        if editor.exec()!=QDialog.DialogCode.Accepted:
            editor.deleteLater()
            return False
        draft[bid] = copy.deepcopy(editor.value)
        editor.deleteLater()
    desired.clear()
    desired.update(draft)
    return True
