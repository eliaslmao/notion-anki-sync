import copy
import importlib.util
import json
import pathlib
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
import ssl
import socket

import sys, types
package = types.ModuleType('core_test')
package.__path__ = [str(pathlib.Path(__file__).parent)]
sys.modules['core_test'] = package
spec = importlib.util.spec_from_file_location('core_test.core', pathlib.Path(__file__).with_name('core.py'))
c = importlib.util.module_from_spec(spec)
sys.modules['core_test.core'] = c
spec.loader.exec_module(c)


def rt(text):
    return [{'type':'text','text':{'content':text}}] if text else []


def block(t, text='', children=None, number=1):
    return dict(id=f'{number:032x}', type=t, has_children=bool(children), _children=children or [], **{t:{'rich_text':rt(text)}})


def image(number=2):
    b = block('image', number=number)
    b['image'] = {'type':'external','external':{'url':'https://example.org/p.png'},'caption':rt('A & B')}
    return b


class Tests(unittest.TestCase):
    def test_safe_network_diagnostics(self):
        secret = 'https://example.org/private?signature=DO_NOT_PRINT'
        for status in (400,401,403,404,429,500):
            for url, stage in [('https://api.notion.com/v1/blocks/test/children','Notion-API'),(secret,'Bilddownload')]:
                with patch.object(c,'urlopen',side_effect=HTTPError(secret,status,'private message',{},None)):
                    with self.assertRaises(c.SyncError) as raised: c.request(url)
                self.assertIn(f'{stage}: HTTP {status}',str(raised.exception))
                self.assertNotIn('DO_NOT_PRINT',str(raised.exception))
                self.assertNotIn('private message',str(raised.exception))
        for reason, expected in [(ssl.SSLCertVerificationError('private'),'Zertifikat'),(socket.gaierror('private'),'DNS'),(TimeoutError(),'40 Sekunden')]:
            with patch.object(c,'urlopen',side_effect=URLError(reason)):
                with self.assertRaises(c.SyncError) as raised: c.request(secret)
            self.assertIn(expected,str(raised.exception))

    def render(self, children, title='Frage'):
        return c.parse([block('toggle', title, children)], 'a'*32, 'Uni', c.Renderer(lambda u:(b'fake-image','image/png')))['0'*31+'1']

    def test_six_split_cases(self):
        i, p, empty = image(), block('paragraph','Antwort',number=3), block('paragraph',number=4)
        for children, front_count, back_count in [([i,p,i],1,1),([i,i,p],2,0),([empty,i,empty,p],1,0),([p,i],0,1),([block('bulleted_list_item','Liste'),i],0,1),([i,p],1,0)]:
            with self.subTest(children=children):
                v = self.render(children)
                self.assertEqual(v['front'].count('<img '), front_count)
                self.assertEqual(v['back'].count('<img '), back_count)
                if front_count:
                    self.assertIn('A &amp; B',v['front'])

    def test_empty_parent_with_children_starts_back(self):
        v = self.render([block('paragraph', children=[image()])])
        self.assertNotIn('<img ',v['front'])
        self.assertIn('<img ',v['back'])

    def test_formatted_empty_paragraph(self):
        empty = block('paragraph','  ')
        empty['paragraph']['rich_text'][0]['annotations'] = {'bold':True}
        v = self.render([empty,image(),block('paragraph','Antwort')])
        self.assertIn('<img ',v['front'])

    def test_invalid_leaf_and_unsupported(self):
        for children in ([], [image()], [block('unsupported')]):
            with self.assertRaises(c.SyncError): self.render(children)
        self.assertIn('<img ',self.render([image(),block('paragraph','Antwort')],title='')['front'])

    def test_hierarchy_layout_heading_and_subpage(self):
        leaf = block('toggle','Frage',[block('paragraph','Antwort')],3)
        heading = block('heading_2','BPMN',[leaf],2)
        heading['heading_2']['is_toggleable'] = True
        root = block('toggle','Modell::ierung',[block('column',children=[heading],number=9)],1)
        v = c.parse([root,block('child_page',children=[leaf],number=8)],'a'*32,'Uni',c.Renderer())
        self.assertEqual(len(v),1)
        self.assertEqual(next(iter(v.values()))['deck'].count('::'),2)
        self.assertNotIn('[',next(iter(v.values()))['deck'])

    def test_same_topic_titles_have_readable_distinct_names(self):
        themes = [block('toggle','Thema',[block('toggle','Frage',[block('paragraph','Antwort')],number=3)],number=1),
                  block('toggle','Thema',[block('toggle','Frage',[block('paragraph','Antwort')],number=4)],number=2)]
        result = c.parse(themes,'a'*32,'Uni',c.Renderer())
        self.assertEqual({v['deck'] for v in result.values()},{'Uni::Thema','Uni::Thema (2)'})
        self.assertTrue(all(v['topics'][0]['id'] in ('0'*31+'1','0'*31+'2') for v in result.values()))

    def test_plans(self):
        v = dict(block='b',page='p',deck='D',front='F',back='B')
        old = dict(v,managed=True,nid=1)
        self.assertEqual(c.plan({'b':v},{'b':old},{'p'}),[('same','b')])
        for key, action in [('front','update'),('back','update'),('page','update'),('deck','move')]:
            changed = dict(v,**{key:'changed'})
            self.assertEqual(c.plan({'b':changed},{'b':old},{'p','changed'}),[(action,'b')])
        self.assertEqual(c.plan({}, {'b':old},{'p'}),[('delete','b')])
        self.assertEqual(c.plan({}, {'b':old},set()),[])
        self.assertEqual(c.plan({}, {'b':dict(old,managed=False)},{'p'}),[])
        self.assertEqual(len(c.plan({'b':v,'c':v},{},{'p'})),2)

    def test_pagination_failure(self):
        calls = []
        def get(url, headers):
            calls.append(url)
            if len(calls)==2: raise c.SyncError('Second page fails')
            return json.dumps({'results':[],'has_more':True,'next_cursor':'next'}).encode(), 'application/json'
        with self.assertRaises(c.SyncError): c.Fetcher('secret',get).tree('a'*32)
        self.assertEqual(len(calls),2)

    def test_overlap_and_bad_pagination(self):
        payload = {'results':[block('paragraph',number=2)],'has_more':False}
        f = c.Fetcher('secret',lambda *a:(json.dumps(payload).encode(),''))
        f.tree('a'*32)
        with self.assertRaises(c.SyncError): f.tree('b'*32)

    def test_image_error_and_stability(self):
        def fail(*args): raise c.SyncError('download failed')
        with self.assertRaises(c.SyncError):
            c.parse([block('toggle','F',[image(),block('paragraph','B')])],'a'*32,'D',c.Renderer(fail))
        self.assertEqual(self.render([image(),block('paragraph','B')]),self.render([image(),block('paragraph','B')]))


if __name__ == '__main__': unittest.main()
