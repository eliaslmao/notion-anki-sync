"""Shared, scoped Qt presentation; follows Anki appearance without app-wide changes."""
from aqt.qt import QLabel,QFont,QDialogButtonBox,Qt

VARIANTS = {'image':'Bildmasken','images':'Bildmasken','sequence':'Bildreihenfolge'}
LIGHT = dict(bg='#f5f5f7',surface='#ffffff',text='#1d1d1f',secondary='#5c5c63',
             line='#d2d2d7',accent='#0066cc',primary='#0066cc',on_primary='#ffffff',
             hover='#e9e9ed',selected='#e8f1fc',focus='#0066cc',danger='#b42318')
DARK = dict(bg='#1c1c1e',surface='#2c2c2e',text='#f5f5f7',secondary='#b5b5bd',
            line='#48484a',accent='#8ac1ff',primary='#0066cc',on_primary='#ffffff',
            hover='#3a3a3c',selected='#263d56',focus='#8ac1ff',danger='#ff9c94')


def colors(widget,dark=None):
    if dark is None:
        try:
            from aqt.theme import theme_manager
            dark = theme_manager.night_mode
        except Exception:
            dark = widget.palette().window().color().lightness()<128
    return dict(DARK if dark else LIGHT)


def style_dialog(dialog,layout,dark=None):
    p = colors(dialog,dark)
    dialog.setObjectName('nsDialog')
    dialog.setStyleSheet('''
        QDialog#nsDialog { background: %(bg)s; color: %(text)s; }
        QLabel { color: %(text)s; background: transparent; }
        QLabel[role="secondary"] { color: %(secondary)s; }
        QLabel[role="warning"] { color: %(text)s; background: %(surface)s;
            border: 1px solid %(line)s; border-radius: 8px; padding: 12px; }
        QPushButton { color: %(text)s; background: %(surface)s; border: 1px solid %(line)s;
            border-radius: 8px; min-height: 44px; min-width: 44px; padding: 0 14px; }
        QPushButton:hover { background: %(hover)s; }
        QPushButton:pressed { background: %(selected)s; }
        QPushButton:checked { background: %(selected)s; border-color: %(accent)s; }
        QPushButton:focus, QComboBox:focus, QLineEdit:focus, QPlainTextEdit:focus,
        QTableWidget:focus, QGraphicsView:focus { border: 2px solid %(focus)s; }
        QPushButton[role="primary"] { color: %(on_primary)s; background: %(primary)s; border-color: %(primary)s; }
        QPushButton[role="primary"]:hover { border: 2px solid %(focus)s; }
        QPushButton:disabled { color: %(secondary)s; background: %(bg)s; border-color: %(line)s; }
        QPushButton[role="primary"]:disabled { color: %(secondary)s; background: %(bg)s; border-color: %(line)s; }
        QLineEdit, QPlainTextEdit, QComboBox { color: %(text)s; background: %(surface)s;
            border: 1px solid %(line)s; border-radius: 8px; padding: 8px; selection-background-color: %(primary)s;
            selection-color: %(on_primary)s; }
        QLineEdit, QComboBox { min-height: 28px; }
        QComboBox { padding-right: 28px; }
        QComboBox::drop-down { border: none; width: 28px; }
        QComboBox QAbstractItemView { color: %(text)s; background: %(surface)s;
            selection-background-color: %(selected)s; selection-color: %(text)s; }
        QTableWidget { color: %(text)s; background: %(surface)s; gridline-color: %(line)s;
            border: 1px solid %(line)s; border-radius: 8px; selection-background-color: %(selected)s;
            selection-color: %(text)s; }
        QTableWidget::item { padding: 8px; border-bottom: 1px solid %(line)s; }
        QHeaderView::section { color: %(secondary)s; background: %(bg)s; border: none;
            border-bottom: 1px solid %(line)s; padding: 12px 8px; font-weight: 600; }
        QGraphicsView { background: %(surface)s; border: 1px solid %(line)s; border-radius: 8px; }
        QScrollArea { border: none; background: transparent; }
        QWidget#nsPageList { background: %(surface)s; }
        QCheckBox { color: %(text)s; min-height: 44px; spacing: 12px; padding: 4px; }
        QCheckBox:focus { outline: 2px solid %(focus)s; }
        QCheckBox::indicator { width: 20px; height: 20px; }
    ''' % p)
    layout.setContentsMargins(24,24,24,24)
    layout.setSpacing(16)
    return p


def label(text,secondary=False):
    result = QLabel(text)
    result.setTextFormat(Qt.TextFormat.PlainText)
    result.setWordWrap(True)
    if secondary: result.setProperty('role','secondary')
    return result


def heading(layout,title,subtitle=None):
    title_label = label(title)
    title_label.setObjectName('nsHeading')
    font = QFont(title_label.font()); font.setPointSizeF(max(16,font.pointSizeF()*1.5)); font.setWeight(QFont.Weight.DemiBold)
    title_label.setFont(font); title_label.setAccessibleName(title)
    layout.addWidget(title_label)
    if subtitle: layout.addWidget(label(subtitle,True))
    return title_label


def buttons(box,ok=None):
    for role,text in [(QDialogButtonBox.StandardButton.Cancel,'Abbrechen'),(QDialogButtonBox.StandardButton.Close,'Schließen'),(QDialogButtonBox.StandardButton.Save,'Speichern')]:
        button = box.button(role)
        if button: button.setText(text)
    primary = box.button(QDialogButtonBox.StandardButton.Ok) or box.button(QDialogButtonBox.StandardButton.Save)
    if primary:
        if ok: primary.setText(ok)
        primary.setProperty('role','primary')
        primary.setDefault(True)
