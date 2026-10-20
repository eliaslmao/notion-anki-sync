"""Allowlisted technical diagnostics: no exception text, locals or source lines."""
import platform
import traceback
from pathlib import Path
import json


def report(error, stage):
    version = json.loads(Path(__file__).with_name('manifest.json').read_text(encoding='utf-8'))['human_version']
    try:
        from anki import version as anki_version
    except ImportError:
        anki_version = 'unbekannt'
    allowed = {'ui.py','core.py','adapter.py','diagnostics.py','transport.py','deck_names.py','card_types.py','type_models.py','mask_preview.py','mask_state.py','mask_editor.py','card_extras.py','local_masks.py','local_mask_ui.py','reviewer_masks.py','ui_style.py','card_style.py','reviewer_interactions.py'}
    lines = [f'Notion Safe Sync {version}', f'Anki {anki_version}',
             f'Python {platform.python_version()}', f'Phase: {stage}',
             f'Fehlertyp: {type(error).__name__}',
             'Interne Aufrufstellen (ohne Pfade, Quelltext, lokale Variablen):']
    try:
        from aqt.qt import qVersion
        lines.insert(3, f'Qt {qVersion()}')
    except ImportError:
        pass
    for frame in traceback.extract_tb(error.__traceback__):
        name = Path(frame.filename).name
        if name in allowed:
            lines.append(f'  {name}:{frame.lineno}')
    for attribute, label in [('application_error','Anwendungsfehler'),('rollback_error','Rücknahmefehler')]:
        nested = getattr(error, attribute, None)
        if nested is not None:
            lines.append(f'{label}: {type(nested).__name__}')
            for frame in traceback.extract_tb(nested.__traceback__):
                name = Path(frame.filename).name
                if name in allowed:
                    lines.append(f'  {name}:{frame.lineno}')
    lines.append('Keine Token, Konfiguration, URLs oder privaten Inhalte enthalten.')
    return '\n'.join(lines)
