"""1.3 regressions: note-scoped approvals, local edits, headers and Qt editor."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import copy
import importlib.util
import pathlib
import unittest
from unittest.mock import patch
from aqt.qt import QApplication,QDialog,QPointF,Qt
from PyQt6.QtTest import QTest

spec = importlib.util.spec_from_file_location('features_fixtures',pathlib.Path(__file__).with_name('test_types.py'))
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
a,c = f.a,f.c
state = __import__('types_test.mask_state',fromlist=['prepare'])
preview = __import__('types_test.mask_preview',fromlist=['confirm'])
Editor = __import__('types_test.mask_editor',fromlist=['MaskEditor']).MaskEditor
app = QApplication.instance() or QApplication([])


class Features(unittest.TestCase):
    setUp,tearDown,sync = f.Tests.setUp,f.Tests.tearDown,f.Tests.sync
    def test_distinct_notes_identical_masks_need_two_separate_controls(self):
        nodes = [f.fixtures()[5],f.fixtures()[5]]
        values,media = f.parsed(nodes)
        keys = a.approval_keys(values,{})
        self.assertEqual(len(keys),2)
        with self.assertRaises(c.SyncError): a.apply(self.col,values,{'a'*32},{},media,{},[next(iter(keys))])
        self.assertEqual(self.col.find_notes(''),[])
        controls = []
        class FakeEditor:
            def __init__(self,parent,value,data): self.value=copy.deepcopy(value); controls.append(value['block'])
            def exec(self): self.value['_editor_confirmed']=True; return QDialog.DialogCode.Accepted
            def deleteLater(self): pass
        with patch.object(preview,'MaskEditor',FakeEditor):
            self.assertTrue(preview.confirm(None,values,{},media))
        self.assertEqual(len(controls),2)
        self.assertEqual(len(set(controls)),2)
        # A note with two cards was edited only once, not once per card.
        self.sync(values,media)
        fresh,_ = f.parsed(nodes)
        self.assertEqual(a.approval_keys(fresh,a.snapshot(self.col)),set())

    def test_local_geometry_survives_and_source_change_conflicts(self):
        node = f.fixtures()[5]
        values,media = f.parsed([node]); state.prepare(values,{})
        v = values[node['id']]
        v['masks'][0]['x']=22.0; v['_editor_confirmed']=True; state.rebuild(v)
        self.sync(values,media)
        old = a.snapshot(self.col)
        self.assertTrue(old[node['id']]['mask_review']['edited'])
        fresh,media = f.parsed([node]); state.prepare(fresh,old)
        self.assertEqual(fresh[node['id']]['masks'][0]['x'],22)
        self.assertFalse(fresh[node['id']]['_review_required'])
        self.assertEqual(self.sync(fresh,media),{'same':1})
        note_change=copy.deepcopy(node); note_change['_children'].append(f.para('[Header] Neue Quelle'))
        metadata_changed,_=f.parsed([note_change]); state.prepare(metadata_changed,old)
        self.assertTrue(metadata_changed[node['id']]['_review_required'])
        self.assertEqual(metadata_changed[node['id']]['masks'][0]['x'],22)
        node['_children'][1] = f.para('Abdeckung 1: x=12%, y=10%, breite=30%, höhe=15%')
        changed,media = f.parsed([node]); state.prepare(changed,old)
        self.assertTrue(changed[node['id']]['_mask_conflict'])
        self.assertEqual(changed[node['id']]['masks'][0]['x'],12)
        with self.assertRaises(c.SyncError): self.sync(changed,media,approve=False)
        self.assertEqual(a.snapshot(self.col),old)

    def test_local_removal_explicitly_deletes_only_its_card(self):
        node = f.fixtures()[5]
        values,media = f.parsed([node]); self.sync(values,media)
        before = a.snapshot(self.col)
        card = self.col.get_card(before[node['id']]['cards'][2]); card.reps,card.ivl=17,30; self.col.update_card(card)
        fresh,media = f.parsed([node]); state.prepare(fresh,before)
        v=fresh[node['id']]; v['masks']=[v['masks'][1]]; v['_editor_confirmed']=True; state.rebuild(v)
        self.assertEqual(a.migration_details(fresh,before)[0]['removed'],[1])
        with self.assertRaises(c.SyncError): self.sync(fresh,media,approve=False)
        self.sync(fresh,media)
        after = a.snapshot(self.col)[node['id']]
        self.assertEqual(after['cards'],{2:card.id})
        self.assertEqual((self.col.get_card(card.id).reps,self.col.get_card(card.id).ivl),(17,30))
        again,media=f.parsed([node]); self.assertEqual(self.sync(again,media),{'same':1})

    def test_abort_second_dialog_discards_all_drafts(self):
        values,media=f.parsed([f.fixtures()[5],f.fixtures()[5]])
        original=copy.deepcopy(values); calls=[]
        class FakeEditor:
            def __init__(self,parent,value,data): self.value=copy.deepcopy(value); calls.append(1)
            def exec(self):
                self.value['masks'][0]['x']=20
                return QDialog.DialogCode.Accepted if len(calls)==1 else QDialog.DialogCode.Rejected
            def deleteLater(self): pass
        with patch.object(preview,'MaskEditor',FakeEditor): self.assertFalse(preview.confirm(None,values,{},media))
        self.assertEqual(values,original)

    def test_headers_all_types_hidden_on_front_and_do_not_generate_cards(self):
        nodes=f.fixtures()
        for node in nodes:
            header=f.para('[Header] SecretHeader {{c99::keine Karte}} ')
            header['paragraph']['rich_text'].append({'type':'text','text':{'content':'PDF','link':{'url':'https://example.org/source.pdf'}},'annotations':{'bold':True}})
            node['_children'].extend([header,f.block('bulleted_list_item','Quellenliste')])
        values,media=f.parsed(nodes); self.sync(values,media)
        self.assertEqual(len(self.col.find_cards('')),8)
        for note in self.col.find_notes(''):
            for card in self.col.get_note(note).cards():
                self.assertNotIn('SecretHeader',card.question())
                self.assertIn('SecretHeader',card.answer())
                self.assertIn('<details class="ns-header">',card.answer())
                self.assertNotIn('<details class="ns-header" open',card.answer())
                self.assertIn('https://example.org/source.pdf',card.answer())
        self.assertEqual(self.sync(values,media),{'same':7})

    def test_header_cannot_validate_missing_answer_or_cloze(self):
        for node in [f.toggle('Q',f.para('[Header] Antwort?')),
                     f.toggle('[Eingabe] Q',f.para('[Header] A')),
                     f.toggle('[Lücke] Org',f.para('Text'),f.para('[Header] {{c1::A}}'))]:
            with self.assertRaises(c.SyncError): f.parsed([node])
        with self.assertRaises(c.SyncError): f.parsed([f.toggle('Q',f.para('A'),f.para('[Header] H'),f.para('[Header] H2'))])

    def test_header_does_not_change_original_front_image_split(self):
        node=f.toggle('Q',f.image(),f.para('A'),f.para('[Header] Quelle'),f.image())
        values,_=f.parsed([node]); v=values[node['id']]
        self.assertEqual(v['front'].count('<img '),1)
        self.assertEqual(v['back'].count('<img '),0)
        self.assertEqual(v['header'].count('<img '),1)

    def test_header_renders_links_and_script_like_text_safely(self):
        h=f.para('[Header] <script>window.injected=1</script> ')
        h['paragraph']['rich_text'].append({'type':'text','text':{'content':'unsicher','link':{'url':'javascript:alert(1)'}}})
        values,_=f.parsed([f.toggle('Q',f.para('A'),h)])
        header=next(iter(values.values()))['header']
        self.assertIn('&lt;script&gt;',header)
        self.assertNotIn('<script>',header)
        self.assertNotIn('javascript:',header)

    def test_source_image_and_kind_changes_invalidate_review_identity(self):
        node=f.fixtures()[5]; values,media=f.parsed([node]); self.sync(values,media)
        before=a.snapshot(self.col)
        fresh,_=f.parsed([node]); v=fresh[node['id']]; v['image_hash']='different-content'
        state.prepare(fresh,before); self.assertTrue(v['_review_required'])
        fresh,_=f.parsed([node]); v=fresh[node['id']]; v['kind']='sequence'; v['order']=[1,2]
        state.prepare(fresh,before); self.assertTrue(v['_review_required'])

    def test_legacy_header_without_changing_shared_legacy_model(self):
        model=self.col.models.new('Notion-Basic')
        for field in ('Front','Back','NotionID','LastSync'): self.col.models.add_field(model,self.col.models.new_field(field))
        template=self.col.models.new_template('Card'); template['qfmt']='{{Front}}'; template['afmt']='{{FrontSide}}{{Back}}'
        self.col.models.add_template(model,template); self.col.models.add(model)
        node=f.toggle('Q',f.para('A'),f.para('[Header] Quelle'))
        note=self.col.new_note(model); note['Front'],note['Back']='Q','A'; note['NotionID']='https://notion.so/'+'a'*32+'#'+node['id']
        self.col.add_note(note,self.col.decks.id('Synthetic')); cid=note.cards()[0].id
        values,_=f.parsed([node]); self.sync(values)
        self.assertEqual(self.col.get_note(note.id).cards()[0].id,cid)
        self.assertNotIn('Header',[x['name'] for x in self.col.models.get(model['id'])['flds']])
        self.assertIn('Mehr',self.col.get_card(cid).answer())
        self.assertNotIn('Quelle',self.col.get_card(cid).question())
        self.assertEqual(self.sync(values),{'same':1})

    def test_template_upgrade_keeps_unselected_legacy_inline_note_usable(self):
        models=__import__('types_test.type_models',fromlist=['get_model'])
        model=models.get_model(self.col,'cloze_input')  # unupgraded 1.2 native format
        notes=[]
        import json
        for index in (1,2):
            n=self.col.new_note(model); n['Front']='Org'; n['Back']='{{c1::Alt}}'
            n['NotionID']='https://notion.so/'+'a'*32+'#'+f'{index:032x}'
            n['NotionSync']=json.dumps(dict(page=('a' if index==1 else 'b')*32,block=f'{index:032x}',kind='cloze_input',ids=[1]))
            n.tags=[a.TAG]; self.col.add_note(n,self.col.decks.id('Synthetic')); notes.append(n)
        foreign_before=a.snapshot(self.col)[f'{2:032x}']; cid=notes[1].cards()[0].id
        node=f.toggle('[Lücke+Eingabe] Org',f.para('{{c1::Neu}}')); node['id']=f'{1:032x}'
        values,_=f.parsed([node]); self.sync(values)
        self.assertEqual(a.snapshot(self.col)[f'{2:032x}'],foreign_before)
        self.assertIn('[[type:cloze:Back]]',self.col.get_card(cid).question())
        self.assertNotIn('ns-inline-root',self.col.get_card(cid).question().split('</style>')[-1])

    def test_editor_move_resize_remove_undo_cancel_at_two_scales(self):
        values,media=f.parsed([f.fixtures()[5]]); state.prepare(values,{})
        original=copy.deepcopy(next(iter(values.values())))
        for width,height in [(750,560),(1250,850)]:
            editor=Editor(None,original,media[original['image']]); editor.resize(width,height); editor.show(); app.processEvents()
            start=editor.snapshot(); item=editor.items[1]
            point=editor.view.mapFromScene(item.rect().center())
            target=editor.view.mapFromScene(item.rect().center()+QPointF(40,20))
            QTest.mousePress(editor.view.viewport(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
            QTest.mouseMove(editor.view.viewport(),target,40)
            QTest.mouseRelease(editor.view.viewport(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,target)
            app.processEvents()
            self.assertAlmostEqual(editor.snapshot()[0]['x'],start[0]['x']+10,delta=.5)
            editor.undo(); self.assertEqual(editor.snapshot(),start)
            editor.redo(); self.assertNotEqual(editor.snapshot(),start)
            editor.undo(); item=editor.items[1]
            point=editor.view.mapFromScene(item.rect().bottomRight()-QPointF(.5,.5))
            target=editor.view.mapFromScene(item.rect().bottomRight()+QPointF(19.5,9.5))
            QTest.mousePress(editor.view.viewport(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
            QTest.mouseMove(editor.view.viewport(),target,40)
            QTest.mouseRelease(editor.view.viewport(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,target)
            app.processEvents()
            self.assertAlmostEqual(editor.snapshot()[0]['w'],35,delta=.5)
            editor.undo(); self.assertEqual(editor.snapshot(),start)
            # Exercise the actual context-menu handler with a deterministic selection.
            module=__import__('types_test.mask_editor',fromlist=['QMenu'])
            class Event:
                def screenPos(self): return editor.mapToGlobal(editor.rect().center())
                def accept(self): pass
            with patch.object(module.QMenu,'exec',lambda menu,*args:menu.actions()[0]): editor.items[1].contextMenuEvent(Event())
            self.assertEqual([m['id'] for m in editor.snapshot()],[2])
            editor.undo(); self.assertEqual(editor.snapshot(),start)
            editor.reject(); self.assertEqual(original,next(iter(values.values())))
            editor.close()


if __name__=='__main__': unittest.main()
