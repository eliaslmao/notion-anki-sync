"""Read-only Notion acquisition, deterministic rendering and global planning."""
import hashlib
import html
import json
import re
import uuid
import socket
import ssl
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlsplit


class SyncError(Exception):
    pass


class RequestError(SyncError):
    def __init__(self, message, *, retryable=False, status=None, retry_after=None):
        super().__init__(message)
        self.retryable, self.status, self.retry_after = retryable, status, retry_after


def ident(value):
    value = str(value).split('?')[0].rstrip('/').split('#')[-1]
    match = re.search(r'([0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})$', value)
    if not match:
        raise SyncError('Ungültige Notion-ID/URL')
    return uuid.UUID(match[1]).hex


def rich(items):
    out = ''
    for x in items:
        t = x.get('type')
        if t == 'equation':
            s = r'\(' + html.escape(x[t]['expression']) + r'\)'
        elif t in ('text', 'mention'):
            s = html.escape(x.get('plain_text', x.get('text', {}).get('content', ''))).replace('\n', '<br>')
        else:
            raise SyncError('Nicht unterstützter Rich-Text-Typ')
        a = x.get('annotations', {})
        for key, tag in [('bold','strong'),('italic','em'),('underline','u'),('strikethrough','s'),('code','code')]:
            if a.get(key):
                s = f'<{tag}>{s}</{tag}>'
        color = a.get('color', 'default')
        if re.fullmatch(r'(gray|brown|orange|yellow|green|blue|purple|pink|red)(_background)?', color):
            prop = 'background-color' if color.endswith('_background') else 'color'
            s = f'<span style="{prop}:{color.removesuffix("_background")}">{s}</span>'
        link = x.get('href') or x.get('text', {}).get('link', {}) or {}
        if isinstance(link, dict):
            link = link.get('url')
        if link and urlsplit(link).scheme in ('https', 'http', 'mailto'):
            s = f'<a href="{html.escape(link, quote=True)}">{s}</a>'
        out += s
    return out


def usable(s):
    return bool(html.unescape(re.sub('<[^>]+>', '', s)).strip()) or '<img ' in s


def request(url, headers=None):
    api = urlsplit(url).hostname == 'api.notion.com'
    stage = 'Notion-API' if api else 'Bilddownload'
    try:
        with urlopen(Request(url, headers={'User-Agent':'Notion-Safe-Sync/1.1.0', **(headers or {})}), timeout=40) as r:
            data = r.read(32 * 1024 * 1024 + 1)
            if len(data) > 32 * 1024 * 1024:
                raise SyncError('Download überschreitet 32 MiB')
            length = r.headers.get('Content-Length')
            if length and length.isdigit() and int(length) != len(data):
                raise RequestError(f'{stage}: Antwort unvollständig übertragen.',retryable=True)
            return data, r.headers.get_content_type()
    except SyncError:
        raise
    except HTTPError as error:
        status = error.code
        retry_after = error.headers.get('Retry-After') if error.headers else None
        blocked = False
        if api and status == 429:
            try:
                details = json.loads(error.read(32768)).get('additional_data', {})
                blocked = details.get('rate_limit_reason') == 'public_api_request_blocked'
                if retry_after is None:
                    retry_after = details.get('retry_after')
            except Exception:
                pass
        error.close()
        if api:
            hint = {
                400:'Ungültige API-Anfrage. Seiten-ID und Konfiguration prüfen.',
                401:'Integration-Token fehlt, ist ungültig oder wurde widerrufen. Token in der Add-on-Konfiguration prüfen.',
                403:'Der Integration fehlen Leserechte. Verbindung und Berechtigungen in Notion prüfen.',
                404:'Seite/Block nicht gefunden oder für die Integration nicht freigegeben. Seiten-ID und die Verbindung der Seite zur Integration prüfen.',
                429:'Notion begrenzt gerade die Anfragen. Kurz warten und erneut synchronisieren.',
            }.get(status, 'Notion ist vorübergehend nicht erreichbar.' if status >= 500 else 'API-Anfrage wurde abgelehnt.')
        else:
            hint = 'Bildzugriff verweigert oder Download-Link abgelaufen. Sync erneut starten, damit Notion einen frischen Link liefert.' if status in (401,403,404) else 'Bildserver hat den Download abgelehnt. Später erneut versuchen.'
        if blocked:
            hint = 'Notion hat den API-Zugriff eingeschränkt. Wiederholen hilft nicht; Integration und Notion-Support prüfen.'
        raise RequestError(f'{stage}: HTTP {status}. {hint}', status=status, retry_after=retry_after,
                           retryable=status in (429,500,502,503,504,529) and not blocked) from None
    except HTTPException:
        raise RequestError(f'{stage}: Verbindung während der Übertragung unterbrochen.',retryable=True) from None
    except (URLError, OSError) as error:
        reason = getattr(error, 'reason', error)
        if isinstance(reason, ssl.SSLCertVerificationError):
            hint = 'TLS-Zertifikat konnte nicht geprüft werden. Systemdatum, Anki-Update und HTTPS-Prüfung durch Proxy/Virenschutz prüfen. Zertifikatsprüfung bleibt aktiviert.'
        elif isinstance(reason, (TimeoutError, socket.timeout)):
            hint = 'Zeitüberschreitung nach 40 Sekunden. Verbindung prüfen und erneut versuchen.'
        elif isinstance(reason, socket.gaierror):
            hint = 'Servername konnte nicht aufgelöst werden (DNS). Internet-/DNS-Verbindung prüfen.'
        elif isinstance(reason, ssl.SSLError):
            hint = 'TLS-Verbindung fehlgeschlagen. Proxy/VPN und HTTPS-Prüfung prüfen.'
        else:
            hint = 'Verbindung fehlgeschlagen. Internet, Firewall, VPN oder Proxy prüfen.'
        raise RequestError(f'{stage}: {hint}', retryable=not isinstance(reason, (ssl.SSLError, PermissionError))) from None
    except Exception:
        # Do not echo exception strings: they can contain signed URLs or secrets.
        raise SyncError(f'{stage}: Unerwarteter Fehler beim Lesen der Antwort. Keine Karten geändert.') from None


class Fetcher:
    def __init__(self, token, get=request):
        self.get = get
        self.headers = {'Authorization': 'Bearer ' + token, 'Notion-Version': '2022-06-28'}
        self.seen = set()

    def tree(self, parent):
        result, cursor, cursors = [], None, set()
        while True:
            query = {'page_size': 100}
            if cursor:
                query['start_cursor'] = cursor
            try:
                data, _ = self.get('https://api.notion.com/v1/blocks/' + parent + '/children?' + urlencode(query), self.headers)
            except SyncError as error:
                raise SyncError(str(error) + '\nBetroffener Notion-Block: ' + parent) from None
            try:
                payload = json.loads(data)
            except (ValueError, UnicodeError):
                raise SyncError('Ungültige oder unvollständige API-Antwort: ' + parent) from None
            if not isinstance(payload, dict):
                raise SyncError('Ungültige API-Antwort: ' + parent)
            if not isinstance(payload.get('results'), list) or not isinstance(payload.get('has_more'), bool):
                raise SyncError('Unvollständige API-Antwort: ' + parent)
            for b in payload['results']:
                bid = ident(b['id'])
                if bid in self.seen:
                    raise SyncError('Überlappende Quellen oder doppelte Block-ID: ' + bid)
                self.seen.add(bid)
                b['id'] = bid
                b['_children'] = self.tree(bid) if b.get('has_children') and b['type'] not in ('child_page', 'child_database') else []
                result.append(b)
            if not payload['has_more']:
                return result
            cursor = payload.get('next_cursor')
            if not cursor or cursor in cursors:
                raise SyncError('Ungültige Paginierung: ' + parent)
            cursors.add(cursor)


def is_toggle(b):
    t = b['type']
    return t == 'toggle' or (t in ('heading_1','heading_2','heading_3') and b[t].get('is_toggleable'))


def has_toggle(blocks):
    return any(is_toggle(b) or has_toggle(b.get('_children', [])) for b in blocks)


class Renderer:
    def __init__(self, get=request):
        self.get, self.media = get, {}

    def block(self, b):
        t, children = b['type'], b.get('_children', [])
        d = b.get(t, {})
        text = rich(d.get('rich_text', []))
        nested = ''.join(self.block(c) for c in children)
        if t == 'image':
            url = d.get(d.get('type'), {}).get('url')
            if not url or urlsplit(url).scheme != 'https':
                raise SyncError('Ungültige Bildquelle: ' + b['id'])
            try:
                data, mime = self.get(url)
            except SyncError as error:
                raise SyncError(str(error) + '\nBildblock: ' + b['id']) from None
            ext = {'image/png':'png','image/jpeg':'jpg','image/gif':'gif','image/webp':'webp','image/svg+xml':'svg'}.get(mime)
            if not data or not ext:
                raise SyncError('Ungültiges Bildformat: ' + b['id'])
            name = 'notion_' + hashlib.sha256(data).hexdigest() + '.' + ext
            self.media[name] = data
            return '<figure><img src="' + name + '"><figcaption>' + rich(d.get('caption', [])) + '</figcaption></figure>'
        tags = {'paragraph':'p','heading_1':'h1','heading_2':'h2','heading_3':'h3','quote':'blockquote','callout':'aside','table':'table','column_list':'div','column':'div'}
        if t in tags:
            tag = tags[t]
            return f'<{tag}>{text}{nested}</{tag}>'
        if t in ('bulleted_list_item', 'numbered_list_item', 'to_do'):
            tag = 'ol' if t == 'numbered_list_item' else 'ul'
            return f'<{tag}><li>{text}{nested}</li></{tag}>'
        if t == 'table_row':
            return '<tr>' + ''.join('<td>' + rich(c) + '</td>' for c in d['cells']) + '</tr>'
        if t == 'code':
            raw = ''.join(x.get('text', {}).get('content', '') for x in d.get('rich_text', []))
            return '<pre><code>' + html.escape(raw) + '</code></pre>'
        if t == 'equation':
            return r'\[' + html.escape(d['expression']) + r'\]'
        if t == 'divider':
            return '<hr>'
        raise SyncError('Nicht unterstützter Block ' + t + ': ' + b['id'])


def parse(blocks, page, deck, renderer, warnings=None):
    warnings = warnings if warnings is not None else []
    result = {}
    used_names = {}
    def walk(nodes, path, topics=()):
        for b in nodes:
            children = b.get('_children', [])
            if b['type'] in ('child_page', 'child_database'):
                warnings.append('Unterseite/Datenbank separat konfigurieren: ' + b['id'])
                continue
            if not is_toggle(b):
                if children:
                    walk(children, path, topics)
                else:
                    warnings.append('Inhalt außerhalb Blatt übersprungen: ' + b['id'])
                continue
            title = rich(b[b['type']].get('rich_text', []))
            if has_toggle(children):
                plain = html.unescape(re.sub('<[^>]*>', '', title))
                name = re.sub(r'[\x00-\x1f:]', ' ', plain).strip() or 'Thema'
                names = used_names.setdefault(path.casefold(), set())
                display, number = name, 2
                while display.casefold() in names:
                    display = f'{name} ({number})'
                    number += 1
                names.add(display.casefold())
                walk(children, path + '::' + display, topics + ({'id':b['id'],'title':name,'name':display},))
                continue
            from .card_types import title_type, parse_typed
            from .card_extras import split_header
            try:
                children,header = split_header(children,renderer)
            except SyncError as error:
                raise SyncError(str(error)+'\nNotion-Block: '+b['id']) from None
            try:
                kind, clean_title = title_type(b[b['type']].get('rich_text',[]))
            except SyncError as error:
                raise SyncError(str(error)+'\nNotion-Block: '+b['id']) from None
            if kind != 'basic':
                try:
                    value = parse_typed(kind,clean_title,children,renderer)
                except SyncError as error:
                    raise SyncError(str(error)+'\nNotion-Block: '+b['id']) from None
                if b['id'] in result: raise SyncError('Doppelte Identität: '+b['id'])
                result[b['id']] = dict(block=b['id'],page=page,deck=path,root=deck,topics=list(topics),header=header,**value)
                continue
            front, back, answering = title, '', False
            for c in children:
                t = c['type']
                if t == 'paragraph' and not c.get('_children') and not usable(rich(c[t].get('rich_text', []))):
                    continue
                if t != 'image':
                    answering = True
                rendered = renderer.block(c)
                if answering:
                    back += rendered
                else:
                    front += rendered
            if not usable(front) or not usable(back):
                raise SyncError('Ungültige Frage oder leere Antwort: https://notion.so/' + page + '#' + b['id'])
            if b['id'] in result:
                raise SyncError('Doppelte Identität: ' + b['id'])
            result[b['id']] = dict(block=b['id'], page=page, deck=path, front=front, back=back, root=deck, topics=list(topics),header=header)
    walk(blocks, deck)
    return result


def plan(desired, existing, active):
    actions = []
    for bid, value in desired.items():
        old = existing.get(bid)
        if old and old['page'] not in active:
            raise SyncError('Ein ausgewählter Block gehört bisher zu einer nicht ausgewählten Quelle. Beide beteiligten Seiten auswählen, damit die Karte gemeinsam abgeglichen werden kann. Keine Änderungen angewendet.')
        changed = old is not None and (any(old.get(k) != value[k] for k in ('front','back','page')) or any(old.get(k,default) != value.get(k,default) for k,default in [('kind','basic'),('extra',''),('image',''),('ids',[1]),('masks',[]),('mode',''),('order',[]),('header',''),('inline_data',''),('mask_hash','')]))
        actions.append(('new' if old is None else 'update' if changed else 'move' if old['deck'] != value['deck'] or old.get('mixed_decks') else 'same', bid))
    actions.extend(('delete', bid) for bid, old in existing.items() if bid not in desired and old['page'] in active and (old.get('managed') or old.get('legacy')))
    return actions
