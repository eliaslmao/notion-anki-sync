"""Anonymous fixtures for all seven formats and native isolated collections."""
import importlib
import pathlib
import sys
import tempfile
import types
import unittest
import struct
import zlib

package = types.ModuleType('types_test')
package.__path__ = [str(pathlib.Path(__file__).parent)]
sys.modules['types_test'] = package
c = importlib.import_module('types_test.core')
a = importlib.import_module('types_test.adapter')
ct = importlib.import_module('types_test.card_types')
from anki.collection import Collection


def png():
    def chunk(tag,data): return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
    rows = b''.join(b'\0'+bytes([230 if y<100 else 150,230,250])*400 for y in range(200))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',400,200,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')


def rt(text): return [{'type':'text','text':{'content':text}}]
counter = 50
def block(kind,text='',children=None):
    global counter
    counter += 1
    return dict(id=f'{counter:032x}',type=kind,has_children=bool(children),_children=children or [],**{kind:dict(rich_text=rt(text))})
def para(text): return block('paragraph',text)
def image():
    b = block('image')
    b['image'] = dict(type='external',external=dict(url='https://example.org/synthetic.png'),caption=[])
    return b
def toggle(title,*children): return block('toggle',title,list(children))


def fixtures():
    first = 'Abdeckung 1:\n x=10%, y=10%, breite=30%, höhe=15%'
    second = 'Abdeckung 2: x=55%, y=60%, breite=30%, höhe=15%'
    return [toggle('Frage',para('Antwort')),
            toggle('[Eingabe] Hauptstadt?',para('Wien'),para('Zusatzinfo:'),para('Erklärung')),
            toggle('[Lücke] Organisation',para('Die Stadt ist {{c1::Wien}}.')),
            toggle('[Lücke+Eingabe] Organisation',para('Der Planet ist {{c1::Jupiter}}.')),
            toggle('  [Bildlücke] Was fehlt?',image(),para(first)),
            toggle(' [Bildlücken] Was fehlt?',image(),para(first),para(second),para('Modus: Alle verdecken, eine abfragen')),
            toggle('[Bildfolge] Was fehlt?',image(),para(first),para(second),para('Reihenfolge: 1, 2'))]


def parsed(nodes):
    renderer = c.Renderer(lambda *args:(png(),'image/png'))
    result = c.parse(nodes,'a'*32,'Synthetic',renderer)
    return result,renderer.media


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.col = Collection(str(pathlib.Path(self.temp.name)/'collection.anki2'))
    def tearDown(self):
        self.col.close()
        self.temp.cleanup()
    def sync(self,values,media=None,approve=True):
        before = a.snapshot(self.col)
        summary = {}
        a.apply(self.col,values,{'a'*32},before,media or {},summary,a.approval_keys(values,before) if approve else ())
        return summary

    def test_seven_notes_eight_native_cards_and_idempotence(self):
        desired,media = parsed(fixtures())
        self.assertEqual(self.sync(desired,media),{'new':7})
        state = a.snapshot(self.col)
        self.assertEqual(len(state),7)
        self.assertEqual(len(self.col.find_cards('')),8)
        self.assertEqual(self.sync(desired,media),{'same':7})
        for bid,value in desired.items():
            note = self.col.get_note(state[bid]['nid'])
            card = note.cards()[0]
            question = card.question()
            self.assertNotIn('[Eingabe]',question)
            if value.get('kind')=='input':
                self.assertIn('[[type:Back]]',question)
                self.assertNotIn('Erklärung',question)
                self.assertIn('Erklärung',card.answer())
            if value.get('kind')=='cloze_input':
                self.assertIn('ns-inline-input',question)
                self.assertNotIn('[[type:cloze:Back]]',question)
            if value.get('kind') in ('image','images'):
                self.assertIn('image-occlusion-canvas',question)
                result = self.col.get_image_occlusion_note(note.id)
                self.assertTrue(result.HasField('note'))
                self.assertEqual(len(result.note.occlusions),len(value['masks']))
            if value.get('kind')=='sequence': self.assertIn('ns-next',question)

    def test_cloze_stable_ids_and_explicit_card_deletion(self):
        node = toggle('[Lücke] Org',para('{{c1::A}} und {{c3::B}}'))
        values,media = parsed([node])
        self.sync(values,media)
        bid = node['id']
        before = a.snapshot(self.col)[bid]
        card = self.col.get_card(before['cards'][3])
        card.reps,card.ivl = 13,27
        self.col.update_card(card)
        node['_children'] = [para('Korrigiert {{c3::Neu}} und {{c4::C}}')]
        values,_ = parsed([node])
        with self.assertRaises(c.SyncError): self.sync(values,approve=False)
        self.sync(values)
        after = a.snapshot(self.col)[bid]
        self.assertEqual(after['nid'],before['nid'])
        self.assertEqual(after['cards'][3],before['cards'][3])
        self.assertEqual(set(after['cards']),{3,4})
        self.assertEqual((self.col.get_card(card.id).reps,self.col.get_card(card.id).ivl),(13,27))

    def test_mask_move_remove_and_preview_cache(self):
        node = fixtures()[5]
        node['_children'].insert(3,para('Abdeckung 7: x=1%, y=80%, breite=10%, höhe=10%'))
        values,media = parsed([node])
        with self.assertRaises(c.SyncError): self.sync(values,media,approve=False)
        self.sync(values,media)
        before = a.snapshot(self.col)[node['id']]
        learned = self.col.get_card(before['cards'][2])
        learned.reps,learned.ivl = 9,31
        self.col.update_card(learned)
        self.assertFalse(a.approval_keys(values,a.snapshot(self.col)))
        node['_children'][1] = para('Abdeckung 1: x=20%, y=10%, breite=30%, höhe=15%')
        node['_children'].pop(3)
        values,media = parsed([node])
        self.sync(values,media)
        after = a.snapshot(self.col)[node['id']]
        self.assertEqual(set(after['cards']),{1,2})
        self.assertEqual(after['cards'][1],before['cards'][1])
        self.assertEqual(after['cards'][2],before['cards'][2])
        self.assertEqual((self.col.get_card(learned.id).reps,self.col.get_card(learned.id).ivl),(9,31))

    def test_native_grouped_cloze_and_info_split(self):
        node = toggle('[Lücke+Eingabe] Organisation',para('{{c2::A}} und {{c2::B}}'),para('Zusatzinfo: Erklärung'))
        values,_ = parsed([node])
        self.sync(values)
        state = a.snapshot(self.col)[node['id']]
        self.assertEqual(set(state['cards']),{2})
        card = self.col.get_card(state['cards'][2])
        self.assertNotIn('Erklärung',card.question())
        self.assertIn('Erklärung',card.answer())
        self.assertTrue(self.col.extract_cloze_for_typing(card.note()['Back'],2))

    def test_unsafe_type_migration_aborts_without_changes(self):
        node = toggle('[Lücke] Org',para('{{c3::A}}'))
        values,_ = parsed([node])
        self.sync(values)
        before = a.snapshot(self.col)
        node['toggle']['rich_text'] = rt('[Eingabe] Q')
        node['_children'] = [para('A')]
        values,_ = parsed([node])
        with self.assertRaises(c.SyncError): self.sync(values)
        self.assertEqual(a.snapshot(self.col),before)

    def test_image_many_to_single_preserves_explicit_mask_identity(self):
        node = fixtures()[5]
        values,media = parsed([node])
        self.sync(values,media)
        before = a.snapshot(self.col)[node['id']]
        node['toggle']['rich_text'] = rt('[Bildlücke] Aufgabe')
        node['_children'] = [node['_children'][0],node['_children'][2]]
        values,media = parsed([node])
        self.sync(values,media)
        after = a.snapshot(self.col)[node['id']]
        self.assertEqual(after['cards'],{2:before['cards'][2]})
        self.assertEqual(after['nid'],before['nid'])
        self.col.undo()
        self.assertEqual(a.snapshot(self.col)[node['id']],before)

    def test_basic_input_and_cloze_type_changes(self):
        node = toggle('Frage',para('Antwort'))
        values,_ = parsed([node])
        self.sync(values)
        old = a.snapshot(self.col)[node['id']]
        node['toggle']['rich_text'] = rt('[Eingabe] Frage')
        values,_ = parsed([node])
        with self.assertRaises(c.SyncError): self.sync(values,approve=False)
        self.sync(values)
        self.assertEqual(a.snapshot(self.col)[node['id']]['cards'],old['cards'])
        node['toggle']['rich_text'] = rt('[Lücke] Org')
        node['_children'] = [para('{{c1::Antwort}}')]
        values,_ = parsed([node])
        self.sync(values)
        self.assertEqual(a.snapshot(self.col)[node['id']]['cards'],old['cards'])

    def test_validation(self):
        bad = [toggle('[Unbekannt] Q',para('A')),toggle('[Eingabe] Q',para('A\nB')),
               toggle('[Lücke] Q',para('{{c0::A}}')),toggle('[Lücke] Q',para('{{c1::A}')),
               toggle('[Bildlücke] Q',image(),para('Abdeckung 1: x=90%, y=1%, breite=30%, höhe=5%')),
               toggle('[Bildlücke] Q',image(),para('Abdeckung 1: x=1%, y=1%, breite=3%, höhe=5%'),para('Abdeckung 1: x=1%, y=1%, breite=3%, höhe=5%'))]
        for node in bad:
            with self.subTest(node=node['id']):
                with self.assertRaises(c.SyncError): parsed([node])
        self.assertEqual(self.col.find_notes(''),[])

if __name__ == '__main__': unittest.main()
