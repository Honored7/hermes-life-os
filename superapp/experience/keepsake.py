"""
The You room — the person, held.

moments(): achievements as warm one-liners earned from real data. No points,
no streaks that punish; only kept things, and one gentle invitation for the
first thing not yet kept.
export_all(): the whole of the person's data in one honest file.
wipe_all(): truly empties the journal. Bounded and shape-validated: it clears
the stores Motif owns outright (sleep, journal, vitals) and, for the base
memory journal, truncates ONLY top-level files that provably look like a
memory journal — never subdirs (so calendar tokens/caches stay safe).
"""
from __future__ import annotations
from superapp.experience import store
import json
import time
from superapp.experience.insights import get_wins
from superapp.experience import journal
from superapp.experience.insights import _date_of

def _counts() -> dict:
    try:
        mem = store.get_recent_memory(days=3650)
    except Exception:
        mem = []
    feel = sum((1 for e in mem if e.get('type') == 'mood'))
    steady = sum((1 for e in mem if e.get('type') == 'preparation'))
    try:
        wins_n = len(get_wins(limit=1000))
    except Exception:
        wins_n = 0
    try:
        nights = len(store.load_sleep())
    except Exception:
        nights = 0
    try:
        entries = journal.list_entries()
    except Exception:
        entries = []
    pages = sum((1 for e in entries if not e.get('is_dream')))
    dreams = sum((1 for e in entries if e.get('is_dream')))
    try:
        doors = [k for k, v in (store.load_calendar_tokens() or {}).items() if v]
    except Exception:
        doors = []
    return {'feel': feel, 'wins': wins_n, 'steady': steady, 'nights': nights, 'pages': pages, 'dreams': dreams, 'doors': doors}

def moments() -> dict:
    c = _counts()
    out = []

    def add(mid, icon, tone, text):
        out.append({'id': mid, 'icon': icon, 'tone': tone, 'text': text})
    if c['feel'] >= 30:
        add('feel', 'Smiley', 'lantern', f"{c['feel']} check-ins — a month and more of naming your weather. The companion knows your sky.")
    elif c['feel'] >= 7:
        add('feel', 'Smiley', 'lantern', f"{c['feel']} times you named how you feel, instead of carrying it unnamed.")
    elif c['feel'] >= 1:
        add('feel', 'Smiley', 'lantern', f"You named how you feel — {c['feel']} time(s) so far. The first step in being known.")
    if c['wins'] >= 1:
        add('wins', 'Trophy', 'lantern', f"You wrote down {c['wins']} win(s), kept safe for the harder days.")
    if c['steady'] >= 1:
        add('steady', 'Wind', 'sage', f"You steadied yourself before {c['steady']} hard thing(s), on purpose.")
    if c['nights'] >= 7:
        add('nights', 'MoonStars', 'calm', f"{c['nights']} nights watched over — your rest, taken seriously.")
    elif c['nights'] >= 1:
        add('nights', 'MoonStars', 'calm', f"{c['nights']} night(s) logged — the beginning of a rhythm.")
    if c['pages'] >= 1:
        add('pages', 'Feather', 'lantern', f"{c['pages']} page(s) written from the heart.")
    if c['dreams'] >= 1:
        add('dreams', 'Moon', 'calm', f"{c['dreams']} dream(s) kept from fading.")
    if c['doors']:
        add('door', 'CalendarBlank', 'sage', 'You opened a door — your calendar now speaks to the wizard.')
    next_line = None
    if c['feel'] == 0:
        next_line = 'Your first check-in is a one-tap thing on Today — name the weather, and the room starts filling.'
    elif c['wins'] == 0:
        next_line = 'Your first win is waiting to be written down. Even a small one counts.'
    elif c['nights'] == 0:
        next_line = 'Log a night of sleep, and the companion starts watching over your rest.'
    elif c['pages'] == 0:
        next_line = 'A blank page is waiting in your journal, patient as ever.'
    return {'counts': c, 'moments': out, 'next': next_line}

def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

def _valid_date(s):
    from datetime import date
    try:
        date.fromisoformat(s)
        return True
    except Exception:
        return False

def _hour_of(m):
    ts = m.get('ts')
    if isinstance(ts, (int, float)):
        import time
        return time.localtime(ts).tm_hour
    if isinstance(ts, str) and 'T' in ts:
        try:
            return int(ts.split('T')[1][:2])
        except Exception:
            return None
    t = m.get('time')
    if isinstance(t, str) and ':' in t:
        try:
            return int(t.split(':')[0])
        except Exception:
            return None
    return None

def _hour_word(h):
    if 5 <= h <= 11:
        return 'the morning'
    if 12 <= h <= 16:
        return 'the afternoon'
    if 17 <= h <= 22:
        return 'the evening'
    return 'the night'

def _moments(mem):
    out = []
    for m in mem:
        t = m.get('type')
        txt = m.get('content') or ''
        if t in ('checkin', 'mood'):
            out.append({'date': _date_of(m), 'kind': 'presence', 'text': txt or 'you checked in'})
        elif t == 'journal':
            out.append({'date': _date_of(m), 'kind': 'words', 'text': txt[:80] or 'a word you wrote'})
        elif t == 'gratitude':
            items = m.get('items') or []
            out.append({'date': _date_of(m), 'kind': 'light', 'text': ', '.join((str(i) for i in items)) if items else 'a good thing'})
    return out[-24:]

def keepsake():
    """What Motif holds of you — moments, a letter, quiet recognitions."""
    from datetime import date
    from superapp.experience.store import get_recent_memory, load_goals, load_habits
    mem = store.get_recent_memory(days=120) or []
    checkins = [m for m in mem if m.get('type') in ('checkin', 'mood')]
    stresses = [m for m in mem if m.get('type') == 'stress']
    grat = [m for m in mem if m.get('type') == 'gratitude']
    meds = [m for m in mem if m.get('type') == 'meditation']
    days = {d for m in mem for d in [_date_of(m)] if d}
    recognitions = []
    if len(checkins) >= 20:
        recognitions.append(f"you've checked in {len(checkins)} times — showing up is the whole practice.")
    habits = load_habits() or []
    best = next((h for h in habits if (h.get('best_streak') or 0) >= 7), None)
    if best:
        recognitions.append(f"you kept {best.get('name')} for {best.get('best_streak')} days. that's not luck; that's you.")
    goals = load_goals() or []
    completed = [g for g in goals if _num(g.get('progress')) >= 100]
    if completed:
        recognitions.append(f"you've completed {len(completed)} goal(s). finished things live here now.")
    if len(stresses) >= 5:
        recognitions.append(f"you've named your stress {len(stresses)} times instead of carrying it silently.")
    if len(grat) >= 3:
        recognitions.append(f"you've kept {len(grat)} good things. gratitude, practiced.")
    if len(meds) >= 3:
        recognitions.append(f'{len(meds)} moments of stillness, chosen on purpose.')
    try:
        ds = [date.fromisoformat(d) for d in days if _valid_date(d)]
        if ds:
            span = (date.today() - min(ds)).days + 1
            if span >= 3:
                recognitions.append(f"you've been tending this for {span} days.")
    except Exception:
        pass
    letter = ["I've been watching, the way a companion does — not to judge. Just to know you."]
    hours = {}
    for m in checkins:
        h = _hour_of(m)
        if h is not None:
            hours[h] = hours.get(h, 0) + 1
    if hours:
        letter.append(f'You most often come to me around {_hour_word(max(hours, key=hours.get))}.')
    active = [h for h in habits if (h.get('streak') or 0) > 0]
    if active:
        letter.append('The thread you keep tending is ' + ', '.join((str(h.get('name')) for h in active[:2])) + '.')
    if stresses:
        letter.append("And on the heavy days, you didn't hide the weight — you named it. That takes more courage than it sounds like.")
    letter.append("Whatever the numbers say, the pattern I see is someone trying. That isn't small. That's everything.")
    self_knowledge = []
    try:
        from superapp.experience.insights import mirror
        for t in (mirror().get('threads') or [])[:2]:
            if t.get('text'):
                self_knowledge.append(t['text'])
    except Exception:
        pass
    return {'moments': _moments(mem), 'letter': letter, 'recognitions': recognitions[:6], 'self_knowledge': self_knowledge, 'presence': {'checkins': len(checkins), 'days': len(days)}}
