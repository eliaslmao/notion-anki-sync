"""Offline-only 1.4 tests with synthetic collections and native Qt dialogs."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import copy
import importlib.util
import pathlib
import unittest
from unittest.mock import patch
from aqt.qt import QApplication,QDialog,QTimer,QTableWidget,QPushButton,QPointF,QGraphicsView

spec=importlib.util.spec_from_file_location('local_fixtures',pathlib.Path(__file__).with_name('test_types.py'))
f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
a=f.a
local=__import__('types_test.local_masks',fromlist=['save'])
ui=__import__('types_test.local_mask_ui',fromlist=['select'])
Editor=__import__('types_test.mask_editor',fromlist=['MaskEditor']).MaskEditor
app=QApplication.instance() or QApplication([])
from aqt.qt import QFontDatabase,QFont
if pathlib.Path('C:/Windows/Fonts/arial.ttf').exists():
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/arial.ttf')
    app.setFont(QFont('Arial',10))


class LocalMasks(unittest.TestCase):
    setUp,tearDown,sync=f.Tests.setUp,f.Tests.tearDown,f.Tests.sync
    def setup_images(self):
        self.nodes=f.fixtures()[4:]; values,media=f.parsed(self.nodes)
        self.sync(values,media)
        return values,media
    def draft(self,bid):
        before,value,image=local.read_local(self.col,a.snapshot(self.col)[bid]['nid'])
        value['masks'][0]['x']+=5
        return before,value,image

    def test_offline_list_select_all_none_multiple_and_single(self):
        self.setup_images()
        with patch.object(f.c,'request',side_effect=AssertionError('No network')):
            values,errors=local.candidates(self.col)
            self.assertEqual(errors,[]); self.assertEqual(len(values),3)
            def choose_all():
                d=app.activeModalWidget(); t=d.findChild(QTableWidget)
                self.assertEqual(t.rowCount(),3)
                buttons={b.text():b for b in d.findChildren(QPushButton)}
                buttons['Alle auswählen'].click(); self.assertEqual(len(t.selectionModel().selectedRows()),3)
                buttons['Auswahl aufheben'].click(); self.assertEqual(len(t.selectionModel().selectedRows()),0)
                buttons['Alle auswählen'].click(); d.accept()
            QTimer.singleShot(30,choose_all)
            self.assertEqual(len(ui.select(None,values)),3)
            def choose_one():
                d=app.activeModalWidget(); d.findChild(QTableWidget).selectRow(1); d.accept()
            QTimer.singleShot(30,choose_one); self.assertEqual(len(ui.select(None,values)),1)

    def test_geometry_preserves_all_ids_schedule_and_source_sync(self):
        values,media=self.setup_images(); bid=self.nodes[1]['id']
        before=a.snapshot(self.col); original=before[bid]
        for cid in original['cards'].values():
            card=self.col.get_card(cid); card.reps=13; card.ivl=27; self.col.update_card(card)
        before,v,_=self.draft(bid)
        with patch.object(f.c,'request',side_effect=AssertionError('No network')):
            local.save(self.col,before,{bid:v})
        after=a.snapshot(self.col)[bid]
        self.assertEqual(after['nid'],original['nid']); self.assertEqual(after['cards'],original['cards'])
        for cid in after['cards'].values(): self.assertEqual((self.col.get_card(cid).reps,self.col.get_card(cid).ivl),(13,27))
        fresh,_=f.parsed(self.nodes); local.prepare(fresh,a.snapshot(self.col))
        self.assertEqual(fresh[bid]['masks'][0]['x'],15)
        self.assertFalse(fresh[bid]['_review_required']); self.assertEqual(self.sync(fresh,media),{'same':3})
        changed=copy.deepcopy(self.nodes); changed[1]['_children'][1]=f.para('Abdeckung 1: x=20%, y=10%, breite=30%, höhe=15%')
        fresh,_=f.parsed(changed); local.prepare(fresh,a.snapshot(self.col))
        self.assertTrue(fresh[bid]['_review_required']); self.assertTrue(fresh[bid]['_mask_conflict'])

    def test_delete_requires_exact_card_confirmation_and_undo(self):
        self.setup_images(); bid=self.nodes[1]['id']; before,v,_=self.draft(bid)
        v['masks']=v['masks'][1:]; local.rebuild(v)
        with self.assertRaises(f.c.SyncError): local.save(self.col,before,{bid:v})
        self.assertEqual(a.snapshot(self.col)[bid],before[bid])
        removed=before[bid]['cards'][1]
        local.save(self.col,before,{bid:v},[removed])
        self.assertEqual(a.snapshot(self.col)[bid]['cards'],{2:before[bid]['cards'][2]})
        self.col.undo(); self.assertEqual(a.snapshot(self.col)[bid],before[bid])

    def test_sequence_remove_preserves_single_card_and_order(self):
        self.setup_images(); bid=self.nodes[2]['id']; before,v,_=self.draft(bid)
        v['masks']=v['masks'][1:]; local.rebuild(v)
        local.save(self.col,before,{bid:v})
        after=a.snapshot(self.col)[bid]; self.assertEqual(after['cards'],before[bid]['cards']); self.assertEqual(after['order'],[2])

    def test_missing_corrupt_media_or_masks_no_write(self):
        self.setup_images(); bid=self.nodes[0]['id']; nid=a.snapshot(self.col)[bid]['nid']
        before,v,image=local.read_local(self.col,nid)
        path=pathlib.Path(self.col.media.dir())/v['image']; path.unlink()
        with self.assertRaisesRegex(f.c.SyncError,'Originalbild fehlt'): local.read_local(self.col,nid)
        path.write_bytes(image+b'changed')
        with self.assertRaisesRegex(f.c.SyncError,'Maskendaten'): local.read_local(self.col,nid)
        self.assertEqual(a.snapshot(self.col)[bid],before[bid])

    def test_noop_does_not_write_or_create_undo_entry(self):
        self.setup_images(); bid=self.nodes[0]['id']; before,v,_=self.draft(bid)
        v['masks']=copy.deepcopy(before[bid]['masks'])
        with patch.object(self.col,'update_note',side_effect=AssertionError('no write')),patch.object(self.col,'add_custom_undo_entry',side_effect=AssertionError('no undo')):
            self.assertIsNone(local.save(self.col,before,{bid:v}))

    def test_stale_or_ambiguous_draft_rejected(self):
        self.setup_images(); bid=self.nodes[1]['id']; before,v,_=self.draft(bid)
        v['masks'][0]['id']=77
        with self.assertRaises(f.c.SyncError): local.save(self.col,before,{bid:v})
        before,v,_=self.draft(bid)
        n=self.col.get_note(before[bid]['nid']); n['Front']='Changed'; self.col.update_note(n)
        with self.assertRaisesRegex(f.c.SyncError,'seit der Vorschau'): local.save(self.col,before,{bid:v})
        duplicate=self.col.new_note(n.note_type()); duplicate.fields=n.fields[:]; duplicate.tags=n.tags[:]
        self.col.add_note(duplicate,self.col.decks.id('Synthetic'))
        with self.assertRaisesRegex(f.c.SyncError,'Mehrdeutige Quellidentität'): local.read_local(self.col,n.id)

    def test_failure_second_note_rolls_back_first(self):
        self.setup_images(); before1,v1,_=self.draft(self.nodes[0]['id']); before2,v2,_=self.draft(self.nodes[1]['id'])
        before=dict(before1,**before2); drafts={v1['block']:v1,v2['block']:v2}
        real=self.col.update_note; calls=[]
        def fail(n):
            calls.append(n.id)
            if len(calls)==2: raise RuntimeError('synthetic write failure')
            return real(n)
        with patch.object(self.col,'update_note',side_effect=fail):
            with self.assertRaises(RuntimeError): local.save(self.col,before,drafts)
        for bid in before: self.assertEqual(a.snapshot(self.col)[bid],before[bid])

    def test_editor_paint_bounds_and_clean_partial_vs_full_repaint(self):
        self.setup_images(); before,v,image=local.read_local(self.col,a.snapshot(self.col)[self.nodes[1]['id']]['nid'])
        for size in [(600,500),(1250,900)]:
            d=Editor(None,v,image,selected_id=2); d.resize(*size); d.show(); app.processEvents()
            self.assertTrue(d.items[2].isSelected())
            self.assertEqual(d.view.viewportUpdateMode(),QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
            for item in d.items.values():
                r=item.rect(); self.assertTrue(item.boundingRect().contains(r.adjusted(-1,-1,1,1)))
            for action in ['move','se','selection','undo','redo','zoom','resize']:
                if action in ('move','se'):
                    item=d.items[2]; old=d.snapshot(); item.apply_drag(action,item.rect(),QPointF(-40,-10)); d.commit(old)
                elif action=='selection': d.scene.clearSelection(); d.items[1].setSelected(True)
                elif action=='undo': d.undo()
                elif action=='redo': d.redo()
                elif action=='zoom': d.view.scale(.8,.8)
                else: d.resize(800,600)
                app.processEvents(); first=d.view.viewport().grab().toImage()
                d.view.viewport().repaint(); app.processEvents(); clean=d.view.viewport().grab().toImage()
                self.assertEqual(first,clean,action)
                # No blue selection pixels may remain outside current handles.
                bounds=[d.view.mapFromScene(item.boundingRect()).boundingRect().adjusted(-2,-2,2,2) for item in d.items.values() if item.isSelected()]
                ratio=clean.devicePixelRatio()
                for y in range(0,clean.height(),2):
                    for x in range(0,clean.width(),2):
                        color=clean.pixelColor(x,y)
                        if color.red()<40 and 90<color.green()<180 and color.blue()>180:
                            self.assertTrue(any(r.contains(int(x/ratio),int(y/ratio)) for r in bounds),'Blue trail after '+action)
            scratch=pathlib.Path(__file__).parent.parent/'work'; scratch.mkdir(exist_ok=True)
            edge=d.items[1]; edge.apply_drag('move',edge.rect(),QPointF(-10000,-10000))
            d.scene.clearSelection(); edge.setSelected(True); app.processEvents()
            visible=d.view.mapFromScene(edge.boundingRect()).boundingRect()
            self.assertTrue(d.view.viewport().rect().contains(visible),'Image-edge handles clipped')
            d.grab().save(str(scratch/('mask-editor-scale-'+os.environ.get('QT_SCALE_FACTOR','1')+'.png')))
            d.reject(); d.close()

    def test_template_upgrade_13_without_sync_is_idempotent(self):
        values,_=self.setup_images()
        extras=__import__('types_test.card_extras',fromlist=['ensure_features'])
        before=a.snapshot(self.col)
        for bid,v in values.items():
            n=self.col.get_note(before[bid]['nid']); m=n.note_type()
            m['css']=m['css'].split(extras.HEADER_STYLE_MARK)[0]
            m['css']=m['css'].replace(extras.HEADER_CSS,'.ns-header{margin-top:1.2em;font-size:.85em;opacity:.85}')
            if v['kind'] in ('image','images'):
                m['tmpls'][0]['afmt']+='<div><button id="toggle">Toggle Masks</button></div>'
            self.col.models.update_dict(m)
            extras.ensure_features(self.col,m,v['kind'])
            upgraded=self.col.models.get(m['id'])
            self.assertIn(extras.HEADER_STYLE_MARK,upgraded['css'])
            self.assertNotIn('id="toggle"',upgraded['tmpls'][0]['afmt'])
            with patch.object(self.col.models,'update_dict',side_effect=AssertionError('No repeated update')):
                extras.ensure_features(self.col,upgraded,v['kind'])
        self.assertEqual(a.snapshot(self.col),before)


if __name__=='__main__': unittest.main()
