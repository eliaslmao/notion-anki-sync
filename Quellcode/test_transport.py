import importlib
import pathlib
import sys
import types
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from io import BytesIO
from http.client import IncompleteRead
import json

p = types.ModuleType('network_test')
p.__path__ = [str(pathlib.Path(__file__).parent)]
sys.modules['network_test'] = p
c = importlib.import_module('network_test.core')
t = importlib.import_module('network_test.transport')


class Clock:
    def __init__(self): self.now = 0
    def clock(self): return self.now
    def sleep(self, seconds): self.now += seconds


class Tests(unittest.TestCase):
    def transport(self,send,**kwargs):
        clock = Clock()
        events = []
        transport = t.Transport(send=send,clock=clock.clock,sleep=clock.sleep,jitter=lambda:0,progress=events.append,**kwargs)
        return transport,clock,events

    def test_rate_limit_exact_request_and_retry_after_125_seconds(self):
        calls = []
        def send(url,headers):
            calls.append((url,headers))
            if len(calls)==1: raise c.RequestError('HTTP 429',retryable=True,status=429,retry_after='125')
            return b'ok','application/json'
        net,clock,events = self.transport(send)
        self.assertEqual(net('https://api.notion.com/v1/blocks/x/children?start_cursor=cursor',{'Authorization':'Bearer synthetic'}),(b'ok','application/json'))
        self.assertEqual(calls[0],calls[1])
        self.assertGreaterEqual(clock.now,125)
        self.assertTrue(any('125 s' in e for e in events))
        self.assertFalse(any('synthetic' in e or 'cursor' in e for e in events))

    def test_dosing_and_network_server_recovery(self):
        responses = [c.RequestError('Network',retryable=True),c.RequestError('HTTP 503',retryable=True,status=503), (b'ok','json'),(b'ok','json')]
        def send(*args):
            result = responses.pop(0)
            if isinstance(result,Exception): raise result
            return result
        net,clock,events = self.transport(send)
        net('https://api.notion.com/x')
        before = clock.now
        net('https://api.notion.com/y')
        self.assertGreaterEqual(clock.now-before,0.399)
        self.assertTrue(any('HTTP 503' in e for e in events))

    def test_limit_and_non_retryable(self):
        for retryable,expected in [(True,5),(False,1)]:
            calls = []
            def send(*args):
                calls.append(1)
                raise c.RequestError('HTTP error',retryable=retryable,status=500 if retryable else 401)
            net,_,_ = self.transport(send)
            with self.assertRaises(c.SyncError): net('https://api.notion.com/x')
            self.assertEqual(len(calls),expected)

    def test_cancel_during_wait(self):
        clock = Clock()
        net = t.Transport(send=lambda *a: (_ for _ in ()).throw(c.RequestError('HTTP 429',retryable=True,status=429,retry_after='90')),clock=clock.clock,sleep=clock.sleep,cancelled=lambda:clock.now>=3,jitter=lambda:0)
        with self.assertRaises(c.SyncError): net('https://api.notion.com/x')
        self.assertEqual(clock.now,3)

    def test_real_error_classification(self):
        for code, retryable in [(401,False),(403,False),(404,False),(429,True),(529,True),(503,True)]:
            with patch.object(c,'urlopen',side_effect=HTTPError('https://private',code,'SECRET',{'Retry-After':'70'},BytesIO(b'{}'))):
                with self.assertRaises(c.RequestError) as result: c.request('https://api.notion.com/x')
            self.assertEqual(result.exception.retryable,retryable)
            self.assertEqual(result.exception.retry_after,'70')
            self.assertNotIn('SECRET',str(result.exception))
        body = json.dumps({'additional_data':{'rate_limit_reason':'public_api_request_blocked'}}).encode()
        with patch.object(c,'urlopen',side_effect=HTTPError('https://private',429,'SECRET',{},BytesIO(body))):
            with self.assertRaises(c.RequestError) as result: c.request('https://api.notion.com/x')
        self.assertFalse(result.exception.retryable)

    def test_pagination_retries_same_cursor_without_duplicate_blocks(self):
        calls = []
        def send(url, headers):
            calls.append(url)
            if len(calls)==2: raise c.RequestError('HTTP 429',retryable=True,status=429,retry_after='2')
            more = len(calls)==1
            result = {'results':[{'id':('a' if more else 'b')*32,'type':'paragraph','paragraph':{'rich_text':[]}}], 'has_more':more,'next_cursor':'second' if more else None}
            return json.dumps(result).encode(),'json'
        net,_,_ = self.transport(send)
        tree = c.Fetcher('synthetic',net).tree('f'*32)
        self.assertEqual(len(tree),2)
        self.assertEqual(calls[1],calls[2])

    def test_interrupted_transfer_and_invalid_json_abort(self):
        with patch.object(c,'urlopen',side_effect=IncompleteRead(b'PRIVATE')):
            with self.assertRaises(c.RequestError) as result: c.request('https://api.notion.com/x')
        self.assertTrue(result.exception.retryable)
        self.assertNotIn('PRIVATE',str(result.exception))
        for payload in (b'PRIVATE non-json',b'[]',b'null'):
            with self.assertRaises(c.SyncError): c.Fetcher('synthetic',lambda *args:(payload,'json')).tree('a'*32)

if __name__ == '__main__': unittest.main()
