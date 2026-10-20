"""Local selection/editor orchestration. Network code is deliberately absent."""
import copy
import html
import re
from aqt.qt import (QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QDialogButtonBox,
                    QTableWidget,QTableWidgetItem,QAbstractItemView,QTimer,QHeaderView)
from aqt.operations import QueryOp,CollectionOp
from aqt.utils import showInfo,askUser
from . import local_masks
from .core import SyncError
from .mask_editor import MaskEditor,LABELS
from .ui_style import style_dialog,heading,buttons as style_buttons


def select(parent,values):
    dialog = QDialog(parent); dialog.setWindowTitle('Bilder auswählen')
    layout = QVBoxLayout(dialog)
    style_dialog(dialog,layout)
    heading(layout,'Bilder auswählen','Welche Bildaufgaben möchtest du bearbeiten?')
    controls = QHBoxLayout()
    all_button,none_button = QPushButton('Alle auswählen'),QPushButton('Auswahl aufheben')
    controls.addWidget(all_button); controls.addWidget(none_button); layout.addLayout(controls)
    table = QTableWidget(len(values),3)
    table.setHorizontalHeaderLabels(['Aufgabe','Stapel','Variante'])
    table.setAccessibleName('Bildaufgaben auswählen')
    table.setAccessibleDescription('Mit Strg oder Umschalt mehrere Aufgaben auswählen.')
    table.setShowGrid(False)
    table.verticalHeader().hide()
    table.verticalHeader().setDefaultSectionSize(52)
    table.verticalHeader().setMinimumSectionSize(48)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    keys = list(values)
    for row,bid in enumerate(keys):
        v = values[bid][1]
        title = html.unescape(re.sub('<[^>]*>','',v['front'])).strip()
        for column,text in enumerate([title,v['deck'],LABELS[v['kind']]]):
            item = QTableWidgetItem(text); item.setToolTip(text); table.setItem(row,column,item)
    table.horizontalHeader().setStretchLastSection(False)
    table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Interactive)
    table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents)
    table.setColumnWidth(1,200)
    layout.addWidget(table,1)
    all_button.clicked.connect(table.selectAll); none_button.clicked.connect(table.clearSelection)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
    style_buttons(buttons,'Bearbeiten')
    layout.addWidget(buttons)
    buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
    def update(): buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(table.selectionModel().selectedRows()))
    table.itemSelectionChanged.connect(update); update()
    dialog.setMinimumSize(560,440); dialog.resize(960,560)
    if dialog.exec()!=QDialog.DialogCode.Accepted: return []
    return [keys[i.row()] for i in sorted(table.selectionModel().selectedRows(),key=lambda i:i.row())]


def start(nid=None,selected_id=None,reviewer=None):
    from . import ui
    mw = ui.mw
    if ui.busy: return
    if not mw.col: return
    ui.busy = True
    ui.phase_set('Lokale Bildmasken bearbeiten')
    if reviewer: reviewer._clear_auto_advance_timers()
    def resume():
        if reviewer and mw.state=='review' and mw.reviewer is reviewer and reviewer.card and reviewer.card.nid==nid:
            if reviewer.state=='answer': reviewer._auto_advance_to_question_if_enabled()
            else: reviewer._auto_advance_to_answer_if_enabled()
    def end():
        ui.busy = False
        QTimer.singleShot(0,resume)
    def failed(error):
        ui.finish_error(error)
        QTimer.singleShot(0,resume)
    def loaded(result):
        try:
            values,errors = result
            if errors: showInfo('\n\n'.join(errors),parent=mw,textFormat='plain')
            if not values:
                if not errors: showInfo('Noch keine Bildaufgaben vorhanden. Importiere zuerst Bilder aus Notion.',parent=mw)
                end(); return
            keys = list(values) if nid is not None else select(mw,values)
            if not keys: end(); return
            before,drafts = {},{}
            for bid in keys:
                original = values[bid][0][bid]
                current,value,image = local_masks.read_local(mw.col,original['nid'])
                if current[bid]!=original: raise SyncError('Sammlung seit Auswahl verändert. Bitte erneut öffnen.')
                editor = MaskEditor(mw,value,image,selected_id=selected_id if nid is not None else None)
                try:
                    if editor.exec()!=QDialog.DialogCode.Accepted: end(); return
                    drafts[bid] = copy.deepcopy(editor.value); before[bid] = original
                finally: editor.deleteLater()
            drafts = local_masks.changed(before,drafts)
            if not drafts: end(); return
            details = local_masks.deletion_details(before,drafts)
            approved = []
            if details:
                message = 'Vorschau: Folgende Karten werden einschließlich ihres Lernfortschritts entfernt:\n'
                for d in details:
                    message += '\nNotiz '+str(d['nid'])+': Karten-IDs '+str(d['card_ids'])+' · Abdeckungs-IDs '+str(d['removed'])
                    approved.extend(d['card_ids'])
                if not askUser(message+'\n\nDiese Karten ausdrücklich löschen und alle Entwürfe speichern?',parent=mw): end(); return
            def done(_):
                end()
                # Initiator suppresses the Reviewer's normal queue reset. Keep
                # the same card and side; never rate it or request nextCard().
                if reviewer and mw.state=='review' and reviewer.card and reviewer.card.nid==nid:
                    if reviewer.card.id in approved:
                        mw.moveToState('overview')
                        showInfo('Die gerade angezeigte Karte wurde wie bestätigt entfernt. Keine Bewertung vorgenommen und keine nächste Karte aufgerufen.',parent=mw)
                    else: reviewer._redraw_current_card()
            CollectionOp(parent=mw,op=lambda col:local_masks.save(col,before,drafts,approved)).success(done).failure(failed).run_in_background(initiator=reviewer)
        except Exception as error: failed(error)
    def load(col):
        if nid is None: return local_masks.candidates(col)
        before,value,_ = local_masks.read_local(col,nid)
        return {value['block']:(before,value)},[]
    QueryOp(parent=mw,op=load,success=loaded).failure(failed).run_in_background()
