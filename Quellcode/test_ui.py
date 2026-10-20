"""Qt offscreen configuration smoke test; does not launch a personal profile."""
import importlib
import os
import pathlib
import sys
import types
from unittest.mock import patch
from concurrent.futures import Future
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from aqt.qt import QApplication, QMainWindow, QTimer, QDialog, QLineEdit, QPlainTextEdit, QDialogButtonBox, QMenu, QCheckBox, QPushButton

package = types.ModuleType('safe_ui_test')
package.__path__ = [str(pathlib.Path(__file__).parent)]
sys.modules['safe_ui_test'] = package
ui = importlib.import_module('safe_ui_test.ui')
app = QApplication.instance() or QApplication([])
window = QMainWindow()
saved = {}
class Manager:
    def getConfig(self, name): return saved.copy()
    def writeConfig(self,name,value): saved.update(value)
    def allAddons(self): return []
window.addonManager = Manager()
window.form = types.SimpleNamespace(menuTools=QMenu(window))
ui.mw = window
ui.install()
assert len(window.form.menuTools.actions()) == 4
def fill():
    d = app.activeModalWidget()
    assert isinstance(d,QDialog)
    d.findChild(QLineEdit).setText('test-token-not-real')
    d.findChild(QPlainTextEdit).setPlainText('[{"page_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","deck_name":"Uni::Test"}]')
    d.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).click()
QTimer.singleShot(50,fill)
ui.settings()
assert saved['NOTION_TOKEN'] == 'test-token-not-real'
assert saved['PAGES'][0]['deck_name'] == 'Uni::Test'
print('Qt offscreen: menu, configuration dialog, save and validation passed')

# Reproduce user's actual schema: page_id/name but no deck_name.
errors = []
ui.showInfo = lambda message, **kwargs: errors.append(message)
saved['PAGES'] = [{'page_id':'a'*32, 'name':'Synthetic subject'}]
with patch.object(ui,'QueryOp',side_effect=AssertionError('Network must not start')):
    ui.sync()
assert not ui.busy
assert 'deck_name' in errors[-1]
assert 'Eintrag 1' in errors[-1]
assert 'KeyError' not in errors[-1]
assert 'Synthetic subject' not in ui.last_diagnostic
assert 'test-token-not-real' not in ui.last_diagnostic

def confirm_draft():
    d = app.activeModalWidget()
    editor = d.findChild(QPlainTextEdit)
    proposed = __import__('json').loads(editor.toPlainText())
    assert proposed[0]['deck_name'] == 'Synthetic subject'
    assert 'deck_name' not in saved['PAGES'][0]  # no silent rewrite before Save
    d.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).click()
QTimer.singleShot(50,confirm_draft)
ui.settings()
assert saved['PAGES'][0]['deck_name'] == 'Synthetic subject'

choices = [dict(page_id='a'*32,deck_name='Uni::A',name='A'),dict(page_id='b'*32,deck_name='Uni::B',name='B')]
def choose_second():
    dialog = app.activeModalWidget()
    checks = dialog.findChildren(QCheckBox)
    assert len(checks) == 2 and all(c.isChecked() for c in checks)
    buttons = dialog.findChild(QDialogButtonBox)
    for b in dialog.findChildren(QPushButton):
        if b.text() == 'Auswahl aufheben': b.click()
    assert not buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled()
    for b in dialog.findChildren(QPushButton):
        if b.text() == 'Alle auswählen': b.click()
    assert all(c.isChecked() for c in checks)
    checks[0].setChecked(False)
    buttons.button(QDialogButtonBox.StandardButton.Ok).click()
QTimer.singleShot(50,choose_second)
assert ui.select_pages(choices) == [choices[1]]
QTimer.singleShot(50,lambda: app.activeModalWidget().reject())
assert ui.select_pages(choices) == []
with patch.object(ui,'select_pages',return_value=[]), patch.object(ui,'QueryOp',side_effect=AssertionError('No network after cancellation')):
    ui.sync()
assert not ui.busy
# Subsequent orchestration tests auto-confirm the selection, never remote data.
ui.select_pages = lambda pages: pages

# Exercise real Anki QueryOp orchestration using synthetic task execution.
import aqt
aqt.mw = window
window.col = types.SimpleNamespace(decks=types.SimpleNamespace(all_names_and_ids=lambda:[]))
window._increase_background_ops = lambda: None
window._decrease_background_ops = lambda: None
class Tasks:
    def execute(self, op, done):
        future = Future()
        try: future.set_result(op())
        except Exception as error: future.set_exception(error)
        done(future)
    def with_progress(self, op, done, **kwargs): self.execute(op,done)
    def run_in_background(self, op, done, **kwargs): self.execute(op,done)
window.taskman = Tasks()
confirmations = []
ui.askUser = lambda message: confirmations.append(message) or False
with patch.object(ui.Fetcher,'tree',return_value=[]), patch.object(ui,'snapshot',return_value={}):
    window.form.menuTools.actions()[1].trigger()
assert not ui.busy
assert len(confirmations) == 1
assert 'Vorschau:' in confirmations[0]

# Callback exceptions must reset the lock and expose only allowlisted diagnostics.
secret = 'private content https://host/image?signature=secret token=secret'
with patch.object(ui.Fetcher,'tree',return_value=[]), patch.object(ui,'snapshot',side_effect=RuntimeError(secret)):
    ui.sync()
assert not ui.busy
assert 'RuntimeError' in ui.last_diagnostic
assert 'Sammlung lesen' in ui.last_diagnostic
assert secret not in ui.last_diagnostic
assert secret not in errors[-1]
with patch.object(ui.Fetcher,'tree',return_value=[]), patch.object(ui,'snapshot',return_value={}), patch.object(ui,'askUser',side_effect=RuntimeError(secret)):
    ui.sync()
assert not ui.busy
assert 'Vorschau anzeigen' in ui.last_diagnostic
assert secret not in errors[-1]
print('Preview regression: missing target deck, explicit repair, real QueryOp pipeline, failure diagnostics and lock recovery passed')

# A failure on the second selected page must not reach collection planning/apply.
saved['PAGES'] = choices
with patch.object(ui.Fetcher,'tree',side_effect=[[],ui.SyncError('synthetic incomplete fetch')]), patch.object(ui,'snapshot',side_effect=AssertionError('No plan on incomplete fetch')), patch.object(ui,'CollectionOp',side_effect=AssertionError('No apply on incomplete fetch')):
    ui.sync()
assert not ui.busy
assert 'synthetic incomplete fetch' in errors[-1]
print('Page selection: checkbox controls, cancel without network, incomplete global fetch without collection access passed')

# Progress data cross threads through a lock; all GUI calls stay on the main thread.
from threading import Thread, get_ident
from aqt.qt import QEventLoop
main_thread = get_ident()
updates = []
window.progress = types.SimpleNamespace(want_cancel=lambda:True,update=lambda **kw:updates.append((get_ident(),kw)))
progress = ui.DownloadProgress()
worker = Thread(target=lambda:progress.publish('HTTP 429 – noch 125 s warten'))
worker.start()
worker.join()
loop = QEventLoop()
QTimer.singleShot(260,loop.quit)
loop.exec()
progress.stop()
assert progress.cancelled.is_set()
assert updates and all(tid == main_thread for tid,_ in updates)
assert updates[-1][1]['label'] == 'HTTP 429 – noch 125 s warten'
print('Progress: worker publication, main-thread countdown and cancellation passed')
