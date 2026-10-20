"""Native Qt editor; all geometry is in original image pixels, never view pixels."""
import copy
import html
import re
from aqt.qt import (Qt,QRectF,QPointF,QColor,QPen,QBrush,QFont,QPixmap,QGraphicsRectItem,
    QGraphicsScene,QGraphicsView,QGraphicsItem,QMenu,QDialog,QVBoxLayout,QHBoxLayout,
    QLabel,QPushButton,QDialogButtonBox,QKeySequence,QShortcut,QComboBox)
from aqt.utils import showInfo
from .core import SyncError
from .mask_state import rebuild
from .ui_style import VARIANTS,style_dialog,heading,label,buttons as style_buttons

LABELS = VARIANTS


class ImageView(QGraphicsView):
    def __init__(self,*args):
        super().__init__(*args)
        # Handles use device-sized strokes outside the mask rectangle. Repaint
        # the viewport once per frame, including vacated selection/handle areas.
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

    def fitInView(self,*args):
        items = [item for item in self.scene().items() if isinstance(item,MaskItem)] if self.scene() else []
        for item in items: item.prepareGeometryChange()
        super().fitInView(*args)
        self.viewport().update()

    def scale(self,*args):
        for item in self.scene().items():
            if isinstance(item,MaskItem): item.prepareGeometryChange()
        super().scale(*args)
        self.viewport().update()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.scene(): self.fitInView(self.scene().sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)


class MaskItem(QGraphicsRectItem):
    def __init__(self,editor,mask):
        self.editor,self.mid = editor,mask['id']
        super().__init__(QRectF(mask['x']*editor.image_width/100,mask['y']*editor.image_height/100,
                               mask['w']*editor.image_width/100,mask['h']*editor.image_height/100))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable,True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)

    def handles(self):
        r = self.rect()
        return {'nw':r.topLeft(),'n':QPointF(r.center().x(),r.top()),'ne':r.topRight(),
                'e':QPointF(r.right(),r.center().y()),'se':r.bottomRight(),
                's':QPointF(r.center().x(),r.bottom()),'sw':r.bottomLeft(),'w':QPointF(r.left(),r.center().y())}

    def boundingRect(self):
        # Include the widest cosmetic handle/stroke at the current zoom level.
        padding = 6/max(self.editor.view.transform().m11(),.01)
        return self.rect().adjusted(-padding,-padding,padding,padding)

    def shape(self):
        from aqt.qt import QPainterPath
        path = QPainterPath(); path.addRect(self.boundingRect()); return path

    def handle_at(self,point):
        tolerance = 8/max(self.editor.view.transform().m11(),.01)
        return next((key for key,p in self.handles().items() if abs(p.x()-point.x())<=tolerance and abs(p.y()-point.y())<=tolerance),'move')

    def paint(self,painter,option,widget=None):
        selected = self.isSelected()
        pen = QPen(QColor('#087edb' if selected else '#916100'))
        pen.setCosmetic(True); pen.setWidth(3 if selected else 2)
        painter.setPen(pen); painter.setBrush(QBrush(QColor(255,204,102,225)))
        painter.drawRect(self.rect())
        painter.setPen(QColor('#111111'))
        font = QFont(); font.setPixelSize(max(10,int(14/max(self.editor.view.transform().m11(),.01))))
        painter.setFont(font)
        if self.editor.value['kind']=='sequence':
            painter.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,str(self.editor.mask_number(self.mid)))
        if selected:
            size = 6/max(self.editor.view.transform().m11(),.01)
            painter.setBrush(QBrush(QColor('#ffffff'))); painter.setPen(pen)
            for p in self.handles().values(): painter.drawRect(QRectF(p.x()-size/2,p.y()-size/2,size,size))

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.editor.scene.clearSelection(); self.setSelected(True)
            self.setFocus()
            self.start = event.scenePos(); self.original = QRectF(self.rect())
            self.before = self.editor.snapshot()
            self.handle = self.handle_at(event.scenePos())
            self.editor.update_selection()
            event.accept()
        else: super().mousePressEvent(event)

    def apply_drag(self,handle,original,delta):
        r = QRectF(original)
        dx,dy = delta.x(),delta.y()
        w,h = self.editor.image_width,self.editor.image_height
        if handle=='move':
            r.moveLeft(max(0,min(w-r.width(),r.left()+dx)))
            r.moveTop(max(0,min(h-r.height(),r.top()+dy)))
        else:
            if 'w' in handle: r.setLeft(max(0,min(r.right()-1,r.left()+dx)))
            if 'e' in handle: r.setRight(min(w,max(r.left()+1,r.right()+dx)))
            if 'n' in handle: r.setTop(max(0,min(r.bottom()-1,r.top()+dy)))
            if 's' in handle: r.setBottom(min(h,max(r.top()+1,r.bottom()+dy)))
        self.setRect(r)

    def mouseMoveEvent(self,event):
        if hasattr(self,'start'):
            self.apply_drag(self.handle,self.original,event.scenePos()-self.start)
            event.accept()
        else: super().mouseMoveEvent(event)

    def mouseReleaseEvent(self,event):
        if hasattr(self,'start'):
            if self.editor.snapshot()!=self.before: self.editor.commit(self.before)
            del self.start
            event.accept()
        else: super().mouseReleaseEvent(event)

    def contextMenuEvent(self,event):
        menu = QMenu()
        action = menu.addAction('Maske entfernen')
        action.setEnabled(len(self.editor.items)>1)
        if menu.exec(event.screenPos())==action: self.editor.remove(self.mid)
        event.accept()

    def keyPressEvent(self,event):
        moves = {Qt.Key.Key_Left:QPointF(-1,0),Qt.Key.Key_Right:QPointF(1,0),Qt.Key.Key_Up:QPointF(0,-1),Qt.Key.Key_Down:QPointF(0,1)}
        if event.key() in moves:
            before = self.editor.snapshot()
            delta = moves[event.key()]
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier: delta *= 10
            self.apply_drag('se' if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 'move',self.rect(),delta)
            if self.editor.snapshot()!=before: self.editor.commit(before)
            event.accept()
        elif event.key() in (Qt.Key.Key_Delete,Qt.Key.Key_Backspace):
            self.editor.remove(self.mid); event.accept()
        else: super().keyPressEvent(event)


class MaskEditor(QDialog):
    def __init__(self,parent,value,image_data,selected_id=None):
        super().__init__(parent)
        self.value = copy.deepcopy(value)
        self.history,self.future = [],[]
        caption = 'Bildreihenfolge bearbeiten' if value['kind']=='sequence' else 'Bildmasken bearbeiten'
        self.setWindowTitle(caption)
        layout = QVBoxLayout(self)
        self.colors = style_dialog(self,layout)
        self.heading_label = heading(layout,caption)
        title = html.unescape(re.sub('<[^>]+>','',value['front']))
        self.task_label = label(title)
        layout.addWidget(self.task_label)
        self.info = label('',True); layout.addWidget(self.info)
        if value.get('_mask_conflict'):
            warning = label('Das Bild oder die Masken wurden in Notion geändert. Prüfe den neuen Stand; deine bisherigen Korrekturen wurden nicht übernommen.')
            warning.setProperty('role','warning'); layout.addWidget(warning)
        self.scene = QGraphicsScene(self)
        pixmap = QPixmap()
        if not pixmap.loadFromData(image_data): raise SyncError('Originalbild kann im Maskeneditor nicht geladen werden.')
        self.image_width,self.image_height = pixmap.width(),pixmap.height()
        self.scene.addPixmap(pixmap)
        # Leave room for outward-facing grips even on the original image edge.
        padding = max(self.image_width,self.image_height)*.03
        self.scene.setSceneRect(-padding,-padding,self.image_width+2*padding,self.image_height+2*padding)
        self.view = ImageView(self.scene,self)
        self.view.setAccessibleName('Bildmasken bearbeiten')
        self.view.setAccessibleDescription('Maske auswählen. Pfeiltasten verschieben, Umschalt und Pfeiltasten ändern die Größe. Entf entfernt die ausgewählte Maske.')
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.view,1)
        self.status = label('Wähle eine Maske aus.',True)
        controls = QHBoxLayout()
        self.mask_select = QComboBox()
        self.mask_select.setAccessibleName('Maske auswählen')
        self.mask_select.setToolTip('Maske auswählen · Pfeiltasten zum Verschieben')
        self.mask_select.currentIndexChanged.connect(self.choose_mask)
        controls.addWidget(self.mask_select)
        self.undo_button,self.redo_button = QPushButton('Rückgängig'),QPushButton('Wiederholen')
        self.undo_button.clicked.connect(self.undo); self.redo_button.clicked.connect(self.redo)
        controls.addWidget(self.undo_button); controls.addWidget(self.redo_button)
        self.help_button = QPushButton('Hilfe'); self.help_button.setCheckable(True)
        self.help_button.setAccessibleName('Bedienhinweise anzeigen')
        controls.addStretch(); controls.addWidget(self.help_button); layout.addLayout(controls)
        layout.addWidget(self.status)
        self.help_text = label('Ziehen verschiebt eine Maske. Die Griffe ändern ihre Größe. Rechtsklick oder Entf entfernt sie.\nTastatur: Maske in der Liste wählen, dann Pfeiltasten zum Verschieben. Umschalt + Pfeiltasten ändert die Größe. Strg bewegt in größeren Schritten.',True)
        self.help_text.hide(); layout.addWidget(self.help_text)
        self.help_button.toggled.connect(self.help_text.setVisible)
        QShortcut(QKeySequence.StandardKey.Undo,self).activated.connect(self.undo)
        QShortcut(QKeySequence.StandardKey.Redo,self).activated.connect(self.redo)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        style_buttons(buttons,'Übernehmen')
        buttons.accepted.connect(self.confirm); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.items = {}
        self.scene.selectionChanged.connect(self.update_selection)
        self.restore(value['masks'])
        self.initial_snapshot = self.snapshot()
        if selected_id in self.items:
            self.items[selected_id].setSelected(True)
            self.items[selected_id].setFocus()
        self.setMinimumSize(560,500)
        self.resize(1000,800)

    def snapshot(self):
        return [dict(id=mid,x=round(item.rect().x()/self.image_width*100,6),y=round(item.rect().y()/self.image_height*100,6),w=round(item.rect().width()/self.image_width*100,6),h=round(item.rect().height()/self.image_height*100,6)) for mid,item in sorted(self.items.items())]

    def restore(self,masks):
        selected = next((mid for mid,item in self.items.items() if item.isSelected()),None)
        self.scene.blockSignals(True)
        for item in self.items.values(): self.scene.removeItem(item)
        self.items = {}
        for mask in masks:
            item = MaskItem(self,mask); self.items[mask['id']]=item; self.scene.addItem(item)
        if selected in self.items:
            self.items[selected].setSelected(True); self.items[selected].setFocus()
        self.scene.blockSignals(False)
        self.status.setText('Wähle eine Maske aus.')
        self.refresh()
        self.update_selection()

    def refresh(self):
        if self.value['kind']=='sequence':
            self.info.setText('Reihenfolge: '+' → '.join(str(i+1) for i in range(len(self.items))))
        else: self.info.setText('Masken einzeln abfragen')
        selected = next((mid for mid,item in self.items.items() if item.isSelected()),None)
        self.mask_select.blockSignals(True); self.mask_select.clear()
        self.mask_select.addItem('Maske auswählen',None)
        for mid in self.display_ids(): self.mask_select.addItem(self.mask_label(mid),mid)
        self.mask_select.setCurrentIndex(max(0,self.mask_select.findData(selected)))
        self.mask_select.blockSignals(False)
        self.undo_button.setEnabled(bool(self.history)); self.redo_button.setEnabled(bool(self.future))

    def choose_mask(self,index):
        mid = self.mask_select.itemData(index)
        if mid not in self.items: return
        self.scene.clearSelection(); self.items[mid].setSelected(True)
        self.items[mid].setFocus(); self.view.setFocus()

    def update_selection(self):
        selected = next((mid for mid,item in self.items.items() if item.isSelected()),None)
        self.status.setText(self.mask_label(selected)+' ausgewählt' if selected is not None else 'Wähle eine Maske aus.')
        self.mask_select.blockSignals(True)
        self.mask_select.setCurrentIndex(max(0,self.mask_select.findData(selected)))
        self.mask_select.blockSignals(False)

    def display_ids(self):
        if self.value['kind']=='sequence':
            return [i for i in self.value.get('_source_order',self.value.get('order',[])) if i in self.items]
        return sorted(self.items)

    def mask_number(self,mid):
        return self.display_ids().index(mid)+1

    def mask_label(self,mid):
        return ('Schritt ' if self.value['kind']=='sequence' else 'Maske ')+str(self.mask_number(mid))

    def commit(self,before):
        self.history.append(copy.deepcopy(before)); self.future.clear(); self.refresh()

    def remove(self,mid):
        if len(self.items)<=1:
            self.status.setText('Mindestens eine Maske muss bleiben.'); return
        before = self.snapshot()
        self.scene.removeItem(self.items.pop(mid))
        self.commit(before)

    def undo(self):
        if self.history:
            self.future.append(self.snapshot()); self.restore(self.history.pop())

    def redo(self):
        if self.future:
            self.history.append(self.snapshot()); self.restore(self.future.pop())

    def confirm(self):
        candidate = copy.deepcopy(self.value)
        candidate['masks'] = self.snapshot()
        # Preserve full stored precision for untouched masks and no-op saves.
        original = {m['id']:m for m in self.value['masks']}
        initial = {m['id']:m for m in self.initial_snapshot}
        candidate['masks'] = [copy.deepcopy(original[m['id']]) if m==initial.get(m['id']) else m for m in candidate['masks']]
        try: rebuild(candidate)
        except SyncError as error:
            showInfo(str(error),parent=self,textFormat='plain'); return
        self.value = candidate
        self.value['_editor_confirmed'] = True
        self.accept()

