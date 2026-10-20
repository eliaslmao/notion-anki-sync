"""UI design, contrast, keyboard and safe presentation-only migration."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import copy
import pathlib
import unittest
from unittest.mock import patch
import test_local_masks as fixtures
from aqt.qt import (Qt,QDialog,QLabel,QPushButton,QComboBox,QPointF,QTimer,QTableWidget,
                    QApplication,QFont)
from PyQt6.QtTest import QTest

f=fixtures.f
style=__import__('types_test.ui_style',fromlist=['style_dialog'])
extras=__import__('types_test.card_extras',fromlist=['ensure_features'])
card_style=__import__('types_test.card_style',fromlist=['CARD_CSS'])
Editor=fixtures.Editor
app=fixtures.app
scratch=pathlib.Path(__file__).parent.parent/'work'/'design-ui'
scratch.mkdir(exist_ok=True)


def contrast(a,b):
    def luminance(value):
        rgb=[int(value[i:i+2],16)/255 for i in (1,3,5)]
        rgb=[n/12.92 if n<=.04045 else ((n+.055)/1.055)**2.4 for n in rgb]
        return sum(n*w for n,w in zip(rgb,[.2126,.7152,.0722]))
    x,y=sorted([luminance(a),luminance(b)])
    return (y+.05)/(x+.05)


class Design(unittest.TestCase):
    setUp,tearDown,sync=f.Tests.setUp,f.Tests.tearDown,f.Tests.sync
    def values(self):
        nodes=f.fixtures(); values,media=f.parsed(nodes)
        f.a.approval_keys(values,{})
        return values,media

    def test_two_visible_variants_and_clear_headings(self):
        values,media=self.values()
        self.assertEqual(set(style.VARIANTS.values()),{'Bildmasken','Bildreihenfolge'})
        for v in values.values():
            if v.get('kind') not in style.VARIANTS: continue
            d=Editor(None,v,media[v['image']])
            self.assertEqual(d.heading_label.text(),style.VARIANTS[v['kind']]+' bearbeiten')
            copy_text=d.heading_label.text()+' '+d.info.text()
            for technical in ('Kartentyp','Karten:','IDs:','Bildlücke','Bildfolge'):
                self.assertNotIn(technical,copy_text)
            self.assertFalse(d.help_text.isVisible())
            d.close()

    def test_semantic_palette_contrast(self):
        for palette in (style.LIGHT,style.DARK):
            for bg in ('bg','surface'):
                for fg in ('text','secondary','accent','danger'):
                    self.assertGreaterEqual(contrast(palette[fg],palette[bg]),4.5,(fg,bg,palette))
            self.assertGreaterEqual(contrast(palette['on_primary'],palette['primary']),4.5)

    def test_keyboard_edit_undo_and_help(self):
        values,media=self.values(); v=next(v for v in values.values() if v.get('kind')=='images')
        d=Editor(None,v,media[v['image']]); d.show(); app.processEvents()
        d.mask_select.setCurrentIndex(d.mask_select.findData(2)); app.processEvents()
        self.assertTrue(d.items[2].isSelected())
        original=d.snapshot()
        QTest.keyClick(d.view.viewport(),Qt.Key.Key_Right); app.processEvents()
        self.assertGreater(d.snapshot()[1]['x'],original[1]['x'])
        QTest.keyClick(d.view.viewport(),Qt.Key.Key_Right,Qt.KeyboardModifier.ShiftModifier); app.processEvents()
        self.assertGreater(d.snapshot()[1]['w'],original[1]['w'])
        d.undo(); d.undo(); self.assertEqual(d.snapshot(),original)
        QTest.keyClick(d.help_button,Qt.Key.Key_Space); self.assertTrue(d.help_text.isVisible())
        QTest.keyClick(d.help_button,Qt.Key.Key_Space); self.assertFalse(d.help_text.isVisible())
        self.assertEqual(d.mask_select.accessibleName(),'Maske auswählen')
        self.assertTrue(d.view.accessibleDescription())
        QTest.keyClick(d.view.viewport(),Qt.Key.Key_Tab); app.processEvents()
        self.assertIsNot(app.focusWidget(),d.view.viewport())
        d.reject(); self.assertEqual(v['masks'],original); d.close()

    def test_native_windows_light_dark_sizes_and_large_text(self):
        values,media=self.values()
        for kind in ('images','sequence'):
            v=next(v for v in values.values() if v.get('kind')==kind)
            for dark in (False,True):
                d=Editor(None,v,media[v['image']],selected_id=1)
                style.style_dialog(d,d.layout(),dark=dark)
                for width,height in ((600,700),(1000,860)):
                    d.resize(width,height); d.show(); app.processEvents()
                    self.assertEqual(d.width(),width)
                    for button in d.findChildren(QPushButton):
                        self.assertGreaterEqual(button.height(),44,button.text())
                    for widget in (d.heading_label,d.task_label,d.info,d.view,d.mask_select):
                        self.assertTrue(d.rect().contains(widget.geometry()))
                    d.grab().save(str(scratch/(kind+('-dark' if dark else '-light')+'-'+str(width)+'.png')))
                larger=QFont(d.font()); larger.setPointSizeF(larger.pointSizeF()*1.5); d.setFont(larger)
                d.resize(1000,960); app.processEvents()
                self.assertGreater(d.view.height(),200)
                d.close()

    def test_design_upgrade_preserves_fields_ids_schedule_and_is_idempotent(self):
        values,media=self.values(); self.sync(values,media)
        before=f.a.snapshot(self.col)
        fields={v['nid']:self.col.get_note(v['nid']).fields[:] for v in before.values()}
        cards={cid:self.col.get_card(cid) for v in before.values() for cid in v['cards'].values()}
        for cid,c in cards.items(): c.reps=9; c.ivl=20; self.col.update_card(c)
        for v in before.values():
            n=self.col.get_note(v['nid']); model=n.note_type()
            # Simulate 1.4 by stripping only our presentation wrapper/tokens.
            model['css']=model['css'].split(card_style.STYLE_START)[0]
            prefix=card_style.WRAP_MARK+'<div class="ns-card ns-card-'+v['kind']+'">'
            for key in ('qfmt','afmt'):
                if model['tmpls'][0][key].startswith(prefix): model['tmpls'][0][key]=model['tmpls'][0][key][len(prefix):-6]
            self.col.models.update_dict(model)
            upgraded=extras.ensure_features(self.col,model,v['kind'])
            for key in ('qfmt','afmt'): self.assertEqual(upgraded['tmpls'][0][key].count(card_style.WRAP_MARK),1)
            with patch.object(self.col.models,'update_dict',side_effect=AssertionError('Idempotent update')):
                extras.ensure_features(self.col,upgraded,v['kind'])
        self.assertEqual(f.a.snapshot(self.col),before)
        for nid,expected in fields.items(): self.assertEqual(self.col.get_note(nid).fields,expected)
        for cid in cards: self.assertEqual((self.col.get_card(cid).reps,self.col.get_card(cid).ivl),(9,20))

    def test_local_selection_shows_only_two_variants(self):
        values,media=self.values(); self.sync(values,media)
        candidates,_=fixtures.local.candidates(self.col)
        checked=[]
        def inspect():
            d=app.activeModalWidget(); table=d.findChild(QTableWidget)
            checked.append({table.item(i,2).text() for i in range(table.rowCount())})
            d.grab().save(str(scratch/'selection-light.png'))
            d.reject()
        QTimer.singleShot(80,inspect); fixtures.ui.select(None,candidates)
        self.assertEqual(checked,[{'Bildmasken','Bildreihenfolge'}])


if __name__=='__main__': unittest.main()
