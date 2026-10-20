"""Sequence answer gate and presentation identities; synthetic Qt fixtures."""
import copy
import types
import unittest
from unittest.mock import patch,Mock
import test_design as design

f=design.f
mod=__import__('types_test.reviewer_interactions',fromlist=['answer_gate'])


class Interactions(unittest.TestCase):
    def test_only_sequences_draw_order_numbers_not_stable_ids(self):
        values,media=design.Design.values(self)
        class Painter:
            def __init__(self): self.texts=[]
            def setPen(self,*_): pass
            def setBrush(self,*_): pass
            def setFont(self,*_): pass
            def drawRect(self,*_): pass
            def drawText(self,*args): self.texts.append(args[-1])
        for kind in ('image','images','sequence'):
            v=copy.deepcopy(next(v for v in values.values() if v.get('kind')==kind))
            if kind=='sequence': v['_source_order']=[2,1]
            editor=design.Editor(None,v,media[v['image']])
            painter=Painter(); editor.items[1].paint(painter,None)
            self.assertEqual(painter.texts,['2'] if kind=='sequence' else [])
            self.assertEqual(editor.mask_select.itemData(editor.mask_select.findData(1)),1)
            self.assertEqual(editor.value['masks'],v['masks'])
            if kind=='sequence':
                editor.remove(2); self.assertEqual(editor.mask_number(1),1)
            editor.close()

    def reviewer(self):
        callbacks=[]
        r=types.SimpleNamespace(mw=types.SimpleNamespace(state='review'),state='question',card=types.SimpleNamespace(id=42),
            _clear_auto_advance_timers=Mock(),bottom=types.SimpleNamespace(web=types.SimpleNamespace(eval=Mock())),
            web=types.SimpleNamespace(evalWithCallback=lambda code,callback:callbacks.append(callback)))
        return r,callbacks

    def test_last_step_immediately_shows_answer(self):
        r,callbacks=self.reviewer(); old=Mock()
        with patch.object(mod,'is_sequence',return_value=True):
            for result in ('step','last'):
                mod.answer_gate(r,old)
                self.assertFalse(old.called)
                callbacks.pop()(result)
                if result=='step': self.assertFalse(old.called)
        old.assert_called_once_with(r)

    def test_pending_and_stale_answer_callbacks_do_not_skip(self):
        r,callbacks=self.reviewer(); old=Mock()
        with patch.object(mod,'is_sequence',return_value=True):
            mod.answer_gate(r,old); mod.answer_gate(r,old)
            self.assertEqual(len(callbacks),1)
            r._ns_sequence_generation=1
            callbacks.pop()('complete')
            self.assertFalse(old.called)

    def test_other_cards_keep_native_answer_and_auto_advance(self):
        r,_=self.reviewer(); old=Mock()
        with patch.object(mod,'is_sequence',return_value=False):
            mod.answer_gate(r,old); mod.auto_question(r,old)
        self.assertEqual(old.call_count,2)
        with patch.object(mod,'is_sequence',return_value=True): mod.auto_question(r,old)
        self.assertEqual(old.call_count,2); r._clear_auto_advance_timers.assert_called_once()

    def test_held_key_repeat_is_suppressed_only_for_sequence_questions(self):
        from aqt.qt import QKeyEvent,QEvent,Qt
        ui=__import__('types_test.ui',fromlist=['mw'])
        event=QKeyEvent(QEvent.Type.ShortcutOverride,Qt.Key.Key_Space,Qt.KeyboardModifier.NoModifier,' ',True,1)
        handler=mod.InteractionFilter(design.app)
        with patch.object(ui,'mw',types.SimpleNamespace(reviewer=object())),patch.object(mod,'is_sequence',return_value=True):
            self.assertTrue(handler.eventFilter(None,event))
        with patch.object(ui,'mw',types.SimpleNamespace(reviewer=object())),patch.object(mod,'is_sequence',return_value=False):
            self.assertFalse(handler.eventFilter(None,event))


if __name__=='__main__': unittest.main()
