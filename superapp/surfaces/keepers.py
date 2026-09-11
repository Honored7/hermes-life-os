"""Ported from Motif (feature/wellness-wizard:demo/wellness/you.py (export/wipe half -> surfaces))
onto the superapp layers. Storage flows through superapp.experience.store
(the single demo/ seam); math shared with superapp.intelligence.
Write-side logging moves to superapp.surfaces; LLM reflection moves with
the full wizard. Behaviour of the kept functions is unchanged.
"""
from __future__ import annotations
from superapp.experience import store
import json
import time
from superapp.experience import ingest, journal
from superapp.experience.keepsake import _counts

def export_all() -> dict:
    try:
        mem = store.get_recent_memory(days=3650)
    except Exception:
        mem = []
    try:
        sleep = store.load_sleep()
    except Exception:
        sleep = []
    try:
        entries = journal.list_entries()
    except Exception:
        entries = []
    return {'app': 'Motif', 'exported_at': time.time(), 'counts': _counts(), 'memory': mem, 'sleep': sleep, 'journal': entries, 'vitals': {'heart_rate': ingest._read('heart_rate.json'), 'steps': ingest._read('steps.json')}}

def _clear_memory_journal() -> list:
    """Truncate ONLY top-level files that provably look like the memory journal."""
    cleared = []
    try:
        base = store.HERMES_DIR
        for name in sorted((p.name for p in base.iterdir() if p.is_file())):
            if not (name.endswith('.json') or name.endswith('.jsonl')):
                continue
            p = base / name
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                continue
            sample = data[:5] if isinstance(data, list) else list(data.values())[:5]
            if sample and all((isinstance(e, dict) and 'type' in e for e in sample)):
                p.write_text('[]' if isinstance(data, list) else '{}', encoding='utf-8')
                cleared.append(name)
    except Exception:
        pass
    return cleared

def wipe_all() -> dict:
    cleared = []
    try:
        store.save_sleep([])
        cleared.append('sleep')
    except Exception:
        pass
    try:
        journal.clear_entries()
        cleared.append('journal')
    except Exception:
        pass
    try:
        ingest.clear_vitals()
        cleared.append('vitals')
    except Exception:
        pass
    cleared += ['memory:' + n for n in _clear_memory_journal()]
    return {'cleared': cleared}
