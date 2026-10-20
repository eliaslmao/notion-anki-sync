"""One read-only request queue per run; bounded retries and cancellable waits."""
import math
import random
import time
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from .core import request, RequestError, SyncError


class Transport:
    def __init__(self, *, send=request, progress=lambda message: None,
                 cancelled=lambda: False, clock=time.monotonic, sleep=time.sleep,
                 wall=time.time, jitter=lambda: random.uniform(0,0.25), retries=4):
        self.send, self.progress, self.cancelled = send, progress, cancelled
        self.clock, self.sleep, self.wall, self.jitter = clock, sleep, wall, jitter
        self.retries, self.next_api, self.count = retries, 0, 0

    def check(self):
        if self.cancelled():
            raise SyncError('Abruf abgebrochen. Keine Inhaltsänderungen oder Löschungen angewendet.')

    def wait(self, seconds, reason):
        end = self.clock() + max(0,seconds)
        while self.clock() < end:
            self.check()
            remaining = end - self.clock()
            self.progress(f'{reason} – noch {math.ceil(remaining)} s warten (Abbrechen möglich)')
            self.sleep(min(1,remaining))
        self.check()

    def delay(self, value):
        try:
            seconds = float(value)
            if math.isfinite(seconds) and seconds >= 0:
                return seconds
        except (TypeError, ValueError):
            try:
                return max(0,parsedate_to_datetime(value).timestamp() - self.wall())
            except (TypeError, ValueError, OverflowError):
                pass
        return 0

    def __call__(self, url, headers=None):
        api = urlsplit(url).hostname == 'api.notion.com'
        kind = 'Notion-API' if api else 'Bilddownload'
        for attempt in range(self.retries + 1):
            self.check()
            if api:
                self.wait(self.next_api - self.clock(), 'Abfragen dosieren')
                self.next_api = self.clock() + 0.4
            self.count += 1
            self.progress(f'{kind}: Anfrage {self.count}, Versuch {attempt+1}/{self.retries+1}')
            try:
                result = self.send(url,headers)
                self.check()
                return result
            except RequestError as error:
                if not error.retryable:
                    raise
                if attempt == self.retries:
                    raise SyncError(f'{error}\nNach {self.retries+1} Versuchen abgebrochen. Gesamter Abruf unvollständig; keine Inhaltsänderungen oder Löschungen angewendet.') from None
                seconds = max(self.delay(error.retry_after), min(2**attempt,30)) + self.jitter()
                reason = f'{kind}: HTTP {error.status}' if error.status else f'{kind}: vorübergehender Verbindungsfehler'
                self.wait(seconds, reason + f'; Wiederholung {attempt+1}/{self.retries}')
