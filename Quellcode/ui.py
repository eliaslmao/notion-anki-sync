import json
import sys
from threading import Event, Lock
from pathlib import Path
from aqt import mw
from aqt.qt import QAction, QDialog, QVBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QDialogButtonBox, QCheckBox, QScrollArea, QWidget, QHBoxLayout, QTimer
from aqt.utils import showInfo, askUser
from aqt.operations import QueryOp, CollectionOp
from .core import Fetcher, Renderer, SyncError, ident, parse, plan
from .adapter import snapshot, apply, prepare_decks, migration_details, approval_keys
from .diagnostics import report
from .transport import Transport
from .mask_state import prepare as prepare_masks
from .ui_style import style_dialog,heading,label,buttons as style_buttons,VARIANTS

busy = False
last_diagnostic = ''
phase = 'Start'


def select_pages(pages):
    dialog = QDialog(mw)
    dialog.setWindowTitle('Notion Safe Sync – Seiten auswählen')
    layout = QVBoxLayout(dialog)
    style_dialog(dialog,layout)
    heading(layout,'Seiten auswählen','Nur diese Seiten werden synchronisiert.')
    controls = QHBoxLayout()
    all_button, none_button = QPushButton('Alle auswählen'), QPushButton('Auswahl aufheben')
    controls.addWidget(all_button)
    controls.addWidget(none_button)
    layout.addLayout(controls)
    area = QScrollArea()
    area.setWidgetResizable(True)
    container = QWidget()
    container.setObjectName('nsPageList')
    rows = QVBoxLayout(container)
    checks = []
    for index, page in enumerate(pages,1):
        title = page.get('name') or f'Seite {index}'
        check = QCheckBox(f'{title} → {page["deck_name"]}')
        check.setToolTip('Zum Verschieben einer Aufgabe beide beteiligten Seiten auswählen.')
        check.setChecked(True)
        rows.addWidget(check)
        checks.append(check)
    area.setWidget(container)
    layout.addWidget(area)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    style_buttons(buttons,'Weiter')
    layout.addWidget(buttons)
    def update():
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(any(c.isChecked() for c in checks))
    def choose(value):
        for check in checks:
            check.setChecked(value)
    all_button.clicked.connect(lambda: choose(True))
    none_button.clicked.connect(lambda: choose(False))
    for check in checks:
        check.toggled.connect(update)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    dialog.resize(750,450)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return []
    return [p for p,c in zip(pages,checks) if c.isChecked()]


class DownloadProgress:
    """Worker publishes text; only the Qt timer accesses Anki's GUI."""
    def __init__(self):
        self.cancelled = Event()
        self.lock = Lock()
        self.text = 'Notion-Abruf vorbereiten …'
        self.timer = QTimer(mw)
        self.timer.timeout.connect(self.poll)
        self.timer.start(200)

    def publish(self, text):
        with self.lock:
            self.text = text

    def poll(self):
        if mw.progress.want_cancel():
            self.cancelled.set()
        with self.lock:
            text = self.text
        mw.progress.update(label=text,process=False)

    def stop(self):
        self.timer.stop()
        self.timer.deleteLater()


def diagnostic_dialog():
    d = QDialog(mw)
    d.setWindowTitle('Notion Safe Sync – sichere Fehlerdiagnose')
    layout = QVBoxLayout(d)
    style_dialog(d,layout)
    heading(layout,'Fehlerdiagnose','Technische Angaben ohne Token oder Karteninhalte.')
    text = QPlainTextEdit(last_diagnostic or 'Noch kein Fehler in dieser Anki-Sitzung.')
    text.setReadOnly(True)
    layout.addWidget(text)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    style_buttons(buttons)
    buttons.rejected.connect(d.reject)
    layout.addWidget(buttons)
    d.resize(750,400)
    d.exec()


def guarded(callback, stage):
    def wrapped(*args):
        global phase
        phase = stage
        try:
            return callback(*args)
        except Exception as error:
            finish_error(error)
    return wrapped


def config():
    return mw.addonManager.getConfig(__name__) or {}


def settings():
    c = config()
    d = QDialog(mw)
    d.setWindowTitle('Notion Safe Sync – Konfiguration')
    layout = QVBoxLayout(d)
    style_dialog(d,layout)
    heading(layout,'Notion verbinden')
    token_label = label('Integration-Token')
    layout.addWidget(token_label)
    token = QLineEdit(c.get('NOTION_TOKEN', ''))
    token.setEchoMode(QLineEdit.EchoMode.Password)
    token.setAccessibleName('Notion Integration-Token'); token_label.setBuddy(token)
    token.setPlaceholderText('Token einfügen')
    token.setToolTip('Wird nur lokal in Anki gespeichert.')
    layout.addWidget(token)
    pages_label = label('Seiten')
    layout.addWidget(pages_label)
    draft = json.loads(json.dumps(c.get('PAGES', [])))
    repaired = False
    if isinstance(draft, list):
        for entry in draft:
            if isinstance(entry, dict) and not entry.get('deck_name'):
                entry['deck_name'] = entry.get('name', '')
                repaired = True
    if repaired:
        warning = label('Zielstapel ergänzen: Die vorgeschlagenen Namen vor dem Speichern prüfen.')
        warning.setProperty('role','warning'); layout.addWidget(warning)
    pages = QPlainTextEdit(json.dumps(draft, ensure_ascii=False, indent=2))
    pages_label.setBuddy(pages); pages.setAccessibleName('Notion-Seiten als JSON')
    pages.setToolTip('Je Seite: page_id (URL oder ID), deck_name (Zielstapel), optional is_enabled.')
    pages.setPlaceholderText('[{"page_id": "Notion-URL", "deck_name": "Mein Stapel"}]')
    layout.addWidget(pages)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
    style_buttons(buttons)
    layout.addWidget(buttons)
    def save():
        try:
            p = json.loads(pages.toPlainText())
            validate(p)
            c.update(NOTION_TOKEN=token.text().strip(), PAGES=p)
            mw.addonManager.writeConfig(__name__, c)
            d.accept()
        except SyncError as error:
            showInfo(str(error), textFormat='plain')
        except Exception:
            showInfo('Ungültiges JSON. Erwartet wird eine Liste mit page_id und deck_name.', textFormat='plain')
    buttons.accepted.connect(save)
    buttons.rejected.connect(d.reject)
    d.resize(700, 500)
    d.exec()


def validate(pages):
    if not isinstance(pages, list):
        raise SyncError('PAGES muss eine JSON-Liste sein.')
    seen = set()
    for index, p in enumerate(pages, 1):
        prefix = f'Seitenkonfiguration, Eintrag {index}: '
        if not isinstance(p, dict):
            raise SyncError(prefix + 'Ein Objekt mit page_id und deck_name wird benötigt.')
        if not isinstance(p.get('page_id'), str) or not p['page_id'].strip():
            raise SyncError(prefix + 'page_id fehlt oder ist kein Text.')
        try:
            bid = ident(p['page_id'])
        except SyncError:
            raise SyncError(prefix + 'Ungültige Notion-Seiten-ID/URL.') from None
        if not isinstance(p.get('deck_name'), str) or not p['deck_name'].strip():
            raise SyncError(prefix + 'deck_name (Anki-Zielstapel) fehlt. Unter Extras → Notion Safe Sync: Konfigurationen den Zielstapel ergänzen und speichern. Es wurde keine Verbindung zu Notion aufgebaut.')
        if 'is_enabled' in p and not isinstance(p['is_enabled'], bool):
            raise SyncError(prefix + 'is_enabled muss true oder false sein.')
        if bid in seen or not p['deck_name'].strip() or any(not x.strip() for x in p['deck_name'].split('::')):
            raise SyncError('Doppelte Seite oder ungültiger Hauptstapel')
        seen.add(bid)


def finish_error(error):
    global busy, last_diagnostic
    busy = False
    last_diagnostic = report(error, phase)
    message = str(error) if isinstance(error, SyncError) else 'Sync abgebrochen. Sichere technische Diagnose:\n\n' + last_diagnostic
    message += '\n\nDiagnose erneut öffnen/kopieren: Extras → Notion Safe Sync: Fehlerdiagnose.'
    showInfo(message, textFormat='plain')


def _sync(force_masks=False):
    global busy, phase
    if busy:
        return
    # Prevent the old independent writer from operating on the same cards.
    if '576859862' in sys.modules or ('576859862' in mw.addonManager.allAddons() and mw.addonManager.isEnabled('576859862')):
        showInfo('Bitte zuerst das alte Add-on 576859862 deaktivieren und Anki neu starten. Zugangsdaten vorher über die Übernahmefunktion kopieren.')
        return
    c = config()
    phase = 'Konfiguration prüfen'
    try:
        validate(c.get('PAGES', []))
        active_pages = [p for p in c.get('PAGES', []) if p.get('is_enabled', True)]
        if not active_pages or not c.get('NOTION_TOKEN'):
            raise SyncError('Bitte Token und mindestens eine aktive Seite konfigurieren.')
        if not isinstance(c['NOTION_TOKEN'],str) or any(char.isspace() for char in c['NOTION_TOKEN']) or not c['NOTION_TOKEN'].isascii():
            raise SyncError('Der Token muss ein einzelner ASCII-Text ohne Leerzeichen oder Zeilenumbrüche sein. Bitte die lokale Token-Einstellung prüfen.')
    except Exception as e:
        finish_error(e)
        return
    busy = True
    phase = 'Seitenauswahl'
    active_pages = select_pages(active_pages)
    if not active_pages:
        busy = False
        return
    phase = 'Notion-Abruf und Medienvorbereitung'
    progress = DownloadProgress()
    def failed(error):
        progress.stop()
        finish_error(error)
    def acquire(_):
        section = 'Abruf vorbereiten'
        transport = Transport(progress=lambda text:progress.publish(section + ' | ' + text),cancelled=progress.cancelled.is_set)
        f, r, desired, warnings = Fetcher(c['NOTION_TOKEN'],transport), Renderer(transport), {}, []
        roots = {ident(p['page_id']) for p in active_pages}
        trees = []
        for index,p in enumerate(active_pages,1):
            section = f'Seite {index}/{len(active_pages)} abrufen'
            progress.publish(f'Seite {index}/{len(active_pages)} vollständig abrufen …')
            trees.append((p,f.tree(ident(p['page_id']))))
        for index,(p, tree) in enumerate(trees,1):
            section = f'Seite {index}/{len(trees)}: Inhalte und Bilder'
            transport.check()
            progress.publish(f'Seite {index}/{len(trees)}: Inhalte prüfen und Bilder vorbereiten …')
            desired.update(parse(tree, ident(p['page_id']), p['deck_name'].strip(), r, warnings))
        transport.check()
        return desired, roots, r.media, warnings
    def acquired(data):
        progress.stop()
        if progress.cancelled.is_set():
            raise SyncError('Abruf abgebrochen. Keine Inhaltsänderungen oder Löschungen angewendet.')
        desired, roots, media, warnings = data
        def preview(col):
            before = snapshot(col)
            prepare_decks(col,desired,before)
            prepare_masks(desired,before)
            return before, plan(desired, before, roots)
        def reviewed(result):
            global busy
            from collections import Counter
            before, actions = result
            from .mask_preview import confirm
            if not confirm(mw,desired,before,media,force=force_masks):
                busy = False
                return
            actions = plan(desired,before,roots)
            counts = Counter(a for a, _ in actions)
            migration = [v['nid'] for b, v in before.items() if (b in desired or v['page'] in roots) and not v['managed']]
            names = {'new':'Neu','update':'Aktualisiert','move':'Verschoben','same':'Unverändert','delete':'Gelöscht'}
            message = 'Vorschau:\n' + '\n'.join(f'{names[k]}: {counts[k]}' for k in names if counts[k])
            if not actions: message += 'Keine Änderungen.'
            if migration: message += '\n\nÄltere Aufgaben übernehmen: '+str(migration)
            deletes = [before[b]['nid'] for action,b in actions if action=='delete']
            if deletes: message += '\n\nAufgaben einschließlich Lernfortschritt löschen: '+str(deletes)
            if warnings: message += '\n\nHinweise:\n'+'\n'.join(warnings[:30])
            changes = migration_details(desired,before)
            for change in changes:
                labels = dict(VARIANTS,basic='Frage und Antwort',input='Texteingabe',cloze='Lückentext',cloze_input='Lückentext mit Eingabe')
                message += '\n\nAufgabe '+str(change['nid'])+': '+labels.get(change['old'],change['old'])+' → '+labels.get(change['new'],change['new'])
                if change['card_ids']: message += '\nLernkarten löschen: '+str(change['card_ids'])+' (Masken '+str(change['removed'])+').' 
            message += '\n\nJetzt anwenden?'
            if not askUser(message):
                busy = False
                return
            summary = {}
            def done(_):
                global busy
                busy = False
                showInfo('Synchronisierung abgeschlossen.\n'+' · '.join(f'{names[k]}: {summary.get(k,0)}' for k in names if summary.get(k,0)))
            phase_set('Änderungen anwenden')
            approvals = approval_keys(desired,before)
            CollectionOp(parent=mw, op=lambda col: apply(col, desired, roots, before, media, summary,approvals)).success(guarded(done,'Ergebnis anzeigen')).failure(finish_error).run_in_background()
        phase_set('Sammlung lesen und Vorschau planen')
        QueryOp(parent=mw, op=preview, success=guarded(reviewed,'Vorschau anzeigen')).failure(finish_error).run_in_background()
    try:
        QueryOp(parent=mw, op=acquire, success=guarded(acquired,'Vorschau vorbereiten')).without_collection().with_progress(label='Notion: vollständiger Abruf, Validierung und Bilder …').failure(failed).run_in_background()
    except Exception:
        progress.stop()
        raise


def phase_set(value):
    global phase
    phase = value


sync = guarded(_sync, 'Sync starten')
def _edit_masks():
    from .local_mask_ui import start
    start()

edit_masks = guarded(_edit_masks,'Lokale Bildmasken bearbeiten')
review_source_masks = guarded(lambda:_sync(True),'Bildmasken anhand Notion erneut prüfen')


def upgrade_templates():
    # Open an existing profile without a sync: update only our model templates,
    # through undoable APIs; leave note fields and schedules intact.
    from .card_extras import ensure_features
    from .type_models import NAMES
    if not mw.col: return
    kinds = {name:kind for kind,name in NAMES.items()}
    kinds['Notion Safe Sync'] = 'basic'
    def upgrade(col):
        undo = col.add_custom_undo_entry('Notion Safe Sync: Kartendarstellung aktualisieren')
        try:
            for model in col.models.all():
                if model['name'] in kinds:
                    ensure_features(col,model,kinds[model['name']])
                    col.merge_undo_entries(undo)
            return col.merge_undo_entries(undo)
        except Exception:
            changes = col.merge_undo_entries(undo)
            if col.op_made_changes(changes): col.undo()
            raise
    CollectionOp(parent=mw,op=upgrade).failure(finish_error).run_in_background()


def copy_legacy():
    old = mw.addonManager.getConfig('576859862')
    if not old:
        showInfo('Keine alte Konfiguration gefunden.')
        return
    c = config()
    if c.get('NOTION_TOKEN') or c.get('PAGES'):
        showInfo('Neue Konfiguration ist bereits befüllt. Kein Überschreiben durchgeführt.')
        return
    c['NOTION_TOKEN'] = old.get('NOTION_TOKEN', '')
    c['PAGES'] = old.get('PAGES', [])
    mw.addonManager.writeConfig(__name__, c)
    showInfo('Token und Seiten lokal übernommen. Jetzt altes Add-on deaktivieren und Anki neu starten.')


def install():
    from aqt import gui_hooks
    from .reviewer_masks import install as install_reviewer
    install_reviewer()
    gui_hooks.profile_did_open.append(upgrade_templates)
    for label, callback in [('Notion Safe Sync: Konfigurationen',settings),('Notion Safe Sync: Synchronisation Starten',sync),('Notion Safe Sync: Bildmasken bearbeiten',edit_masks),('Notion Safe Sync: Fehlerdiagnose',diagnostic_dialog)]:
        action = QAction(label, mw)
        action.triggered.connect(lambda checked=False, fn=callback: fn())
        mw.form.menuTools.addAction(action)
