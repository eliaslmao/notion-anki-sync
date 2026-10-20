"""Run against a temporary collection only; requires installed anki Python package."""
import importlib
import pathlib
import sys
import tempfile
import types
import unittest

root = pathlib.Path(__file__).parent
package = types.ModuleType('safe_test')
package.__path__ = [str(root)]
sys.modules['safe_test'] = package
a = importlib.import_module('safe_test.adapter')
from anki.collection import Collection


class Integration(unittest.TestCase):
    def test_readable_decks_migration_collision_and_cleanup(self):
        topic = 'e'*32
        old_path = 'Uni::Thema ['+topic+']'
        v = dict(self.v,deck=old_path)
        self.sync({self.bid:v})
        old = a.snapshot(self.col)[self.bid]
        nid = old['nid']
        cid = self.col.get_note(nid).cards()[0].id
        current = dict(self.v,root='Uni',deck='Uni::Thema',topics=[dict(id=topic,title='Thema',name='Thema')])
        self.assertEqual(self.sync({self.bid:current}),{'move':1})
        self.assertEqual(self.col.decks.name(self.col.get_card(cid).did),'Uni::Thema')
        self.assertIsNone(self.col.decks.id_for_name(old_path))
        self.assertEqual(a.snapshot(self.col)[self.bid]['nid'],nid)
        self.assertEqual(self.sync({self.bid:current}),{'same':1})
        # Foreign deck is not merged or renamed.
        self.col.decks.id('Uni::Fremd')
        other = dict(self.v,block='f'*32,root='Uni',deck='Uni::Fremd',topics=[dict(id='c'*32,title='Fremd',name='Fremd')])
        self.sync({self.bid:current,'f'*32:other})
        self.assertEqual(a.snapshot(self.col)['f'*32]['deck'],'Uni::Fremd (2)')
        self.assertIsNotNone(self.col.decks.id_for_name('Uni::Fremd'))
        self.assertEqual(self.sync({self.bid:current,'f'*32:other}),{'same':2})

    def test_migration_preserves_foreign_cards_and_empty_foreign_children(self):
        topic = 'e'*32
        path = 'Uni::Thema ['+topic+']'
        self.sync({self.bid:dict(self.v,deck=path)})
        n = self.col.new_note(a.model(self.col))
        n['Front'],n['Back'] = 'Foreign','Answer'
        self.col.add_note(n,self.col.decks.id(path))
        self.col.decks.id(path+'::Foreign child')
        v = dict(self.v,root='Uni',topics=[dict(id=topic,title='Thema',name='Thema')])
        self.sync({self.bid:v})
        self.assertIsNotNone(self.col.decks.id_for_name(path))
        self.assertIsNotNone(self.col.decks.id_for_name(path+'::Foreign child'))
        self.assertEqual(self.col.decks.name(self.col.get_note(n.id).cards()[0].did),path)
    def test_selected_sources_protect_unselected_cards_and_ids(self):
        other = 'c'*32
        v2 = dict(self.v,block='d'*32,page=other,deck='Other')
        self.sync({self.bid:self.v,'d'*32:v2},{self.page,other})
        before = a.snapshot(self.col)
        foreign_nid = before['d'*32]['nid']
        foreign_card = self.col.get_note(foreign_nid).cards()[0]
        foreign_fields = self.col.get_note(foreign_nid).fields[:]
        self.sync({}, {self.page})
        after = a.snapshot(self.col)
        self.assertEqual(set(after),{'d'*32})
        self.assertEqual(after['d'*32],before['d'*32])
        self.assertEqual(self.col.get_note(foreign_nid).fields,foreign_fields)
        self.assertEqual(self.col.get_note(foreign_nid).cards()[0].id,foreign_card.id)
        # Cross-source move cannot silently change the unselected origin.
        moved = dict(v2,page=self.page,deck='Uni')
        with self.assertRaises(a.SyncError): self.sync({'d'*32:moved},{self.page})
        self.assertEqual(a.snapshot(self.col),after)
        self.sync({'d'*32:moved},{self.page,other})
        self.assertEqual(a.snapshot(self.col)['d'*32]['nid'],foreign_nid)
        self.assertEqual(self.col.get_note(foreign_nid).cards()[0].id,foreign_card.id)
    def test_large_first_import_72_notes(self):
        desired = {f'{i:032x}':dict(self.v,block=f'{i:032x}') for i in range(1,73)}
        self.assertEqual(self.sync(desired),{'new':72})
        self.assertEqual(len(a.snapshot(self.col)),72)
        self.col.undo()
        self.assertEqual(a.snapshot(self.col),{})

    def test_large_failed_import_rolls_back_everything(self):
        desired = {f'{i:032x}':dict(self.v,block=f'{i:032x}',deck='Uni::Topic'+str(i)) for i in range(1,73)}
        original = self.col.add_note
        count = 0
        def fail_late(note, did):
            nonlocal count
            count += 1
            if count == 65:
                raise RuntimeError('synthetic late failure')
            return original(note,did)
        self.col.add_note = fail_late
        with self.assertRaises(RuntimeError): self.sync(desired)
        self.col.add_note = original
        self.assertEqual(self.col.find_notes(''),[])
        self.assertFalse(any(d.name.startswith('Uni') for d in self.col.decks.all_names_and_ids()))

    def test_large_update_and_move_preserves_ids_and_can_undo(self):
        desired = {f'{i:032x}':dict(self.v,block=f'{i:032x}') for i in range(1,73)}
        self.sync(desired)
        before = a.snapshot(self.col)
        updated = {bid:dict(v,front='Updated',deck='Uni::Changed'+bid) for bid,v in desired.items()}
        self.sync(updated)
        self.assertEqual({b:v['nid'] for b,v in a.snapshot(self.col).items()},{b:v['nid'] for b,v in before.items()})
        self.col.undo()
        self.assertEqual(a.snapshot(self.col),before)

    def test_resume_partial_previous_import_without_duplicates(self):
        desired = {f'{i:032x}':dict(self.v,block=f'{i:032x}') for i in range(1,73)}
        partial = dict(list(desired.items())[:43])
        self.sync(partial)
        before = a.snapshot(self.col)
        self.assertEqual(self.sync(desired),{'same':43,'new':29})
        after = a.snapshot(self.col)
        self.assertEqual(len(after),72)
        for bid, old in before.items():
            self.assertEqual(after[bid]['nid'],old['nid'])
        self.assertEqual(self.sync(desired),{'same':72})

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.col = Collection(str(pathlib.Path(self.temp.name)/'collection.anki2'))
        self.bid, self.page = 'b'*32, 'a'*32
        self.v = dict(block=self.bid,page=self.page,deck='Uni::Test',front='Frage',back='Antwort')

    def tearDown(self):
        self.col.close()
        self.temp.cleanup()

    def sync(self, desired, roots=None):
        summary = {}
        a.apply(self.col, desired, roots or {self.page}, a.snapshot(self.col), {}, summary)
        return summary

    def test_identity_schedule_move_delete_undo(self):
        self.sync({self.bid:self.v})
        nid = a.snapshot(self.col)[self.bid]['nid']
        card = self.col.get_note(nid).cards()[0]
        card.reps, card.ivl, card.due = 12, 20, 42
        self.col.update_card(card)
        cid = card.id
        self.assertEqual(self.sync({self.bid:self.v}),{'same':1})
        v = dict(self.v,front='Korrigiert',deck='Uni::Umbenannt',page='c'*32)
        self.sync({self.bid:v},{self.page,'c'*32})
        self.assertEqual(a.snapshot(self.col)[self.bid]['nid'],nid)
        card = self.col.get_card(cid)
        self.assertEqual((card.reps,card.ivl,card.due),(12,20,42))
        self.assertEqual(self.col.decks.name(card.did),'Uni::Umbenannt')
        # Foreign card in same deck must survive empty source reconciliation.
        n = self.col.new_note(a.model(self.col))
        n['Front'],n['Back'] = 'Fremd','Bleibt'
        self.col.add_note(n,card.did)
        self.sync({}, {'c'*32})
        self.assertEqual(self.col.find_notes(''),[n.id])
        self.col.undo()
        self.assertIn(nid,self.col.find_notes(''))

    def test_disabled_and_leaf_topic(self):
        self.sync({self.bid:self.v})
        self.sync({}, {'d'*32})
        self.assertIn(self.bid,a.snapshot(self.col))
        leaf = dict(self.v,block='e'*32)
        self.sync({'e'*32:leaf})
        self.assertEqual(set(a.snapshot(self.col)),{'e'*32})

    def test_media_offline_preview_and_collision(self):
        import hashlib
        data = b'\x89PNG\r\n\x1a\nfixture'
        name = 'notion_' + hashlib.sha256(data).hexdigest() + '.png'
        self.col.media.write_data(name,b'foreign content')
        v = dict(self.v,front='<img src="'+name+'">')
        summary = {}
        a.apply(self.col,{self.bid:v},{self.page},{},{name:data},summary)
        card = self.col.get_note(a.snapshot(self.col)[self.bid]['nid']).cards()[0]
        self.assertIn('<img ',card.question())
        self.assertIn('Antwort',card.answer())
        self.assertNotIn('https://',card.question())
        self.assertEqual((pathlib.Path(self.col.media.dir())/name).read_bytes(),b'foreign content')
        v = dict(self.v,front='<img src="'+name+'">')
        summary = {}
        a.apply(self.col,{self.bid:v},{self.page},a.snapshot(self.col),{name:data},summary)
        self.assertEqual(summary,{'same':1})

    def test_legacy_migration_duplicate_and_unknown(self):
        m = self.col.models.new('Notion-Basic')
        for name in ('Front','Back','NotionID','LastSync'):
            self.col.models.add_field(m,self.col.models.new_field(name))
        t = self.col.models.new_template('Card')
        t['qfmt'],t['afmt'] = '{{Front}}','{{Back}}'
        self.col.models.add_template(m,t)
        self.col.models.add(m)
        n = self.col.new_note(m)
        n['Front'],n['Back'],n['NotionID'] = 'Alt','Alt','https://notion.so/'+self.page+'#'+self.bid
        self.col.add_note(n,self.col.decks.id('Alt'))
        cid = n.cards()[0].id
        self.sync({self.bid:self.v})
        self.assertEqual(a.snapshot(self.col)[self.bid]['nid'],n.id)
        self.assertEqual(self.col.get_note(n.id).cards()[0].id,cid)
        duplicate = self.col.new_note(m)
        duplicate['Front'],duplicate['NotionID'] = 'Duplikat',n['NotionID']
        self.col.add_note(duplicate,self.col.decks.id('Alt'))
        with self.assertRaises(a.SyncError): a.snapshot(self.col)
        self.col.remove_notes([duplicate.id])
        broken = self.col.new_note(m)
        broken['Front'] = 'Ohne ID'
        self.col.add_note(broken,self.col.decks.id('Alt'))
        with self.assertRaises(a.SyncError): a.snapshot(self.col)

    def test_rollback_failed_move(self):
        self.sync({self.bid:self.v})
        before = a.snapshot(self.col)
        original = self.col.set_deck
        def fail(*args): raise RuntimeError('injected failure')
        self.col.set_deck = fail
        try:
            with self.assertRaises(RuntimeError):
                a.apply(self.col,{self.bid:dict(self.v,front='Änderung',deck='Neu')},{self.page},before,{}, {})
        finally:
            self.col.set_deck = original
        self.assertEqual(a.snapshot(self.col),before)


if __name__ == '__main__': unittest.main()
