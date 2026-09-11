"""
Hermes Life OS — Insights.
The wizard looks across what you've shared and reflects: what's helping,
what you've won, what it notices. Built on demo/storage.py memory.
"""
from __future__ import annotations
from superapp.experience import store
from superapp.intelligence.patterns import pearson as _corr

def get_wins(limit: int=12) -> list:
    wins = [w for w in store.search_memory('win', limit=limit) if w.get('type') == 'win']
    return [{'description': w.get('content') or w.get('description') or 'A win', 'timestamp': w.get('timestamp', '')} for w in wins]

def get_effective_interventions() -> list:
    logs = [item for item in store.search_memory('intervention', limit=50) if item.get('type') == 'intervention']
    by_name: dict = {}
    for item in logs:
        name = item.get('intervention_name') or 'A practice'
        entry = by_name.setdefault(name, {'name': name, 'times_used': 0, 'improvements': [], 'state': item.get('state')})
        entry['times_used'] += 1
        before, after = (item.get('severity_before'), item.get('severity_after'))
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            entry['improvements'].append(before - after)
    result = []
    for name, d in by_name.items():
        avg = round(sum(d['improvements']) / len(d['improvements']), 1) if d['improvements'] else None
        result.append({'name': name, 'times_used': d['times_used'], 'avg_improvement': avg, 'state': d['state']})
    result.sort(key=lambda x: x['avg_improvement'] if x['avg_improvement'] is not None else -99, reverse=True)
    return result[:5]

def _recent_signature() -> str:
    """Cheap fingerprint of the last 7 days; changes whenever new data lands."""
    entries = store.get_recent_memory(days=7)

    def n(t):
        return sum((1 for e in entries if e.get('type') == t))
    last_ts = entries[-1].get('timestamp', '') if entries else ''
    return f"{n('mood')}|{n('intervention')}|{n('win')}|{n('sleep')}|{n('hydration')}|{last_ts}"

def get_insights_summary() -> dict:
    return {'wins': get_wins(), 'effective': get_effective_interventions(), 'signature': _recent_signature()}
STATES = ['good', 'neutral', 'stressed', 'anxious', 'sad', 'angry', 'low_energy', 'lonely']

def mood_weather(days: int=7) -> dict:
    """Distribution of moods over the last N days — the data behind the Today aura."""
    try:
        entries = store.get_recent_memory(days=days)
    except Exception:
        entries = []
    moods = [e for e in entries if e.get('type') == 'mood' and e.get('state')]
    counts = {st: 0 for st in STATES}
    sev = []
    for e in moods:
        st = e.get('state')
        if st in counts:
            counts[st] += 1
        if e.get('severity') is not None:
            try:
                sev.append(float(e['severity']))
            except (TypeError, ValueError):
                pass
    total = sum(counts.values())
    predominant = max(counts, key=counts.get) if total else None
    spread = len([c for c in counts.values() if c > 0])
    temperature = round(sum(sev) / len(sev), 1) if sev else None
    return {'total': total, 'days': days, 'predominant': predominant, 'predominant_count': counts.get(predominant, 0) if predominant else 0, 'spread': spread, 'temperature': temperature, 'counts': counts}
VALENCE = {'good': 2, 'neutral': 1, 'stressed': -1, 'low_energy': -1, 'anxious': -2, 'sad': -2, 'angry': -2, 'lonely': -2}
STATE_WORD = {'good': 'joyful', 'neutral': 'calm', 'stressed': 'stressed', 'anxious': 'anxious', 'sad': 'sad', 'angry': 'angry', 'low_energy': 'drained', 'lonely': 'lonely'}

def _date_of(e) -> str:
    d = e.get('date')
    return str(d) if d else str(e.get('timestamp', ''))[:10]

def mood_trend(days: int=21) -> dict:
    """The emotional mirror: an intensity line (colour = mood) plus a
    valence-based tone-shift verdict that can never contradict it."""
    from datetime import date as _date, timedelta
    try:
        entries = store.get_recent_memory(days=days)
    except Exception:
        entries = []
    rows = []
    for e in entries:
        if e.get('type') != 'mood' or not e.get('state') or e.get('severity') is None:
            continue
        d = _date_of(e)
        if not d:
            continue
        try:
            rows.append((d, e['state'], float(e['severity'])))
        except (TypeError, ValueError):
            continue
    by = {}
    for d, st, sev in rows:
        by.setdefault(d, {'sevs': [], 'states': []})
        by[d]['sevs'].append(sev)
        by[d]['states'].append(st)
    series = []
    for d in sorted(by):
        sevs, states = (by[d]['sevs'], by[d]['states'])
        series.append({'date': d, 'severity': round(sum(sevs) / len(sevs), 1), 'state': max(set(states), key=states.count)})
    series = series[-days:]
    today = _date.today()
    this_rows = [r for r in rows if (today - timedelta(days=6)).isoformat() <= r[0] <= today.isoformat()]
    last_rows = [r for r in rows if (today - timedelta(days=13)).isoformat() <= r[0] <= (today - timedelta(days=7)).isoformat()]

    def vavg(rs):
        return sum((VALENCE.get(st, 0) for _, st, _ in rs)) / len(rs) if rs else None

    def pred(rs):
        sts = [st for _, st, _ in rs]
        return max(set(sts), key=sts.count) if sts else None
    tv, lv = (vavg(this_rows), vavg(last_rows))
    if tv is None or lv is None:
        direction, delta = ('none', None)
    else:
        delta = round(tv - lv, 2)
        direction = 'warmer' if delta >= 0.6 else 'cooler' if delta <= -0.6 else 'holding'
    tw = STATE_WORD.get(pred(this_rows), 'your days')
    lw = STATE_WORD.get(pred(last_rows), 'before')
    verdict = {'none': 'Not quite two weeks of check-ins yet — the mirror is still clearing. Keep naming how you feel, and a shape will form.', 'holding': f'About the same ground as last week — {tw}, holding steady. There is a quiet strength in that consistency.', 'warmer': f'The tone of your week has warmed — {lw} giving way to more {tw}. Whatever you have been doing, some of it is landing.', 'cooler': f'A cooler week than the last — more {tw} than {lw}. That is worth tending gently, not fixing in a hurry.'}[direction]
    this_intensity = round(sum((s for _, _, s in this_rows)) / len(this_rows), 1) if this_rows else None
    return {'series': series, 'direction': direction, 'delta': delta, 'verdict': verdict, 'this_predominant': pred(this_rows), 'last_predominant': pred(last_rows), 'this_intensity': this_intensity, 'this_count': len(this_rows), 'last_count': len(last_rows)}

def mirror():
    """The week's weave, the threads between, and what's rising or easing."""
    from datetime import date, timedelta
    from superapp.experience.store import get_recent_memory, load_fitness, load_focus, load_sleep

    def _n(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0
    days = [(date.today() - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
    mood = {}
    stress = {}
    sleep = {}
    move = {}
    focus = {}
    for e in store.get_recent_memory(days=14) or []:
        d = str(e.get('date') or '')
        if e.get('type') in ('checkin', 'mood'):
            mv = e.get('mood')
            sev = e.get('severity')
            val = _n(mv) if isinstance(mv, (int, float)) else 10 - _n(sev if sev is not None else 5)
            mood.setdefault(d, []).append(val)
        if e.get('type') == 'stress' and e.get('score') is not None:
            stress.setdefault(d, []).append(_n(e.get('score')))
    for x in load_sleep() or []:
        if _n(x.get('hours')) > 0:
            sleep[str(x.get('date') or '')] = _n(x.get('hours'))
    for x in load_fitness() or []:
        move[str(x.get('date') or '')] = move.get(str(x.get('date') or ''), 0) + _n(x.get('duration'))
    for x in load_focus() or []:
        focus[str(x.get('date') or '')] = focus.get(str(x.get('date') or ''), 0) + _n(x.get('duration'))
    mood = {d: sum(v) / len(v) for d, v in mood.items()}
    stress = {d: sum(v) / len(v) for d, v in stress.items()}

    def pair(a, b):
        ds = [d for d in days if d in a and d in b]
        return ([a[d] for d in ds], [b[d] for d in ds])
    threads = []

    def add_thread(an, bn, r, pos, neg):
        if r is None or abs(r) < 0.3:
            return
        threads.append({'a': an, 'b': bn, 'r': round(r, 2), 'strength': round(abs(r), 2), 'text': pos if r > 0 else neg})
    xs, ys = pair(sleep, mood)
    add_thread('sleep', 'mood', _corr(xs, ys), 'On nights you sleep longer, your mood runs brighter. Sleep is your keystone — protect it.', 'Curiously, longer sleep has lined up with lower mood lately. Worth a gentle look.')
    xs, ys = pair(move, mood)
    add_thread('movement', 'mood', _corr(xs, ys), 'Days you move, your mood follows. Motion is medicine for you.', 'Movement and mood have drifted apart lately — rest may matter more than exercise right now.')
    xs, ys = pair(sleep, focus)
    add_thread('sleep', 'focus', _corr(xs, ys), 'Good nights feed your focus. The quiet hours are doing quiet work.', "Focus hasn't tracked sleep lately — something else is holding your attention.")
    xs, ys = pair(stress, sleep)
    add_thread('stress', 'sleep', _corr(xs, ys), 'Low stress and good sleep travel together for you.', 'Heavy-stress days line up with shorter sleep. Tending the mind would tend the night.')
    xs, ys = pair(stress, mood)
    add_thread('stress', 'mood', _corr(xs, ys), 'Calm days and bright days go together for you.', 'When stress rises, your mood dips. Naming the weight is the first kindness.')
    tapestry = []
    for d in days[-7:]:
        tapestry.append({'date': d, 'mood': round(mood[d] / 10, 2) if d in mood else None, 'sleep': round(min(sleep[d] / 9, 1), 2) if d in sleep else None, 'move': round(min(move.get(d, 0) / 60, 1), 2) if d in move else None, 'focus': round(min(focus.get(d, 0) / 120, 1), 2) if d in focus else None, 'calm': round(1 - stress[d] / 10, 2) if d in stress else None})
    this, prev = (days[7:], days[:7])

    def avg(dd, rng):
        vals = [dd[d] for d in rng if d in dd]
        return sum(vals) / len(vals) if vals else None
    trends = []
    for name, dd in [('mood', mood), ('sleep', sleep), ('movement', move), ('focus', focus), ('stress', stress)]:
        a, b = (avg(dd, this), avg(dd, prev))
        if a is None or b is None:
            dir_ = 'steady'
        elif a > b * 1.08:
            dir_ = 'up'
        elif a < b * 0.92:
            dir_ = 'down'
        else:
            dir_ = 'steady'
        trends.append({'dim': name, 'dir': dir_})
    reflection = 'The mirror is still gathering your days. Live a little longer and it will start to speak.'
    question = None
    if threads:
        t = max(threads, key=lambda x: x['strength'])
        reflection = f"The strongest thread I can see is between {t['a']} and {t['b']}. {t['text']}"
        question = f"What would change if you protected your {t['a']} this week?"
    return {'tapestry': tapestry, 'threads': threads, 'trends': trends, 'reflection': reflection, 'question': question}

def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

def _climate_data(lens):
    from datetime import date, timedelta
    from superapp.experience.store import load_sleep, load_fitness, load_focus, load_nutrition, get_recent_memory
    mem = store.get_recent_memory(days=400) or []
    sleep = {}
    stress = {}
    mood = {}
    move = {}
    water = {}
    meals = {}
    focus = {}
    journal = {}
    grat = {}
    for e in mem:
        d = str(e.get('date') or '')
        if not d:
            continue
        t = e.get('type')
        if t in ('checkin', 'mood'):
            mv = e.get('mood')
            sev = e.get('severity')
            val = _num(mv) if isinstance(mv, (int, float)) else 10 - _num(sev if sev is not None else 5)
            mood.setdefault(d, []).append(val)
        elif t == 'stress' and e.get('score') is not None:
            stress.setdefault(d, []).append(_num(e.get('score')))
        elif t == 'journal':
            journal[d] = journal.get(d, 0) + 1
        elif t == 'gratitude':
            grat[d] = grat.get(d, 0) + 1
        elif t == 'hydration':
            water[d] = max(water.get(d, 0), _num(e.get('glasses')))
    for x in load_sleep() or []:
        if _num(x.get('hours')) > 0:
            sleep[str(x.get('date') or '')] = _num(x.get('hours'))
    for x in load_fitness() or []:
        move[str(x.get('date') or '')] = move.get(str(x.get('date') or ''), 0) + _num(x.get('duration'))
    for x in load_focus() or []:
        focus[str(x.get('date') or '')] = focus.get(str(x.get('date') or ''), 0) + _num(x.get('duration'))
    for x in load_nutrition() or []:
        meals[str(x.get('date') or '')] = meals.get(str(x.get('date') or ''), 0) + 1
    mood = {d: sum(v) / len(v) for d, v in mood.items()}
    stress = {d: sum(v) / len(v) for d, v in stress.items()}
    all_days = sorted(set(sleep) | set(mood) | set(move) | set(stress) | set(focus) | set(meals) | set(water) | set(journal) | set(grat))
    if not all_days:
        return None
    today = date.today()
    rng_start = today - timedelta(days=29) if lens == '30' else date.fromisoformat(all_days[0])
    days = [d for d in all_days if date.fromisoformat(d) >= rng_start]
    if not days:
        return None
    now_cut = today - timedelta(days=13)
    now_days = [d for d in days if date.fromisoformat(d) >= now_cut]
    then_days = [d for d in days if date.fromisoformat(d) < now_cut] if lens == '30' else days[:14]

    def avg(series, dl):
        vals = [series[d] for d in dl if d in series]
        return round(sum(vals) / len(vals), 1) if vals else None
    mood_now = [d for d in now_days if d in mood]
    return {'span': len(days), 'first': all_days[0], 'sleep_t': avg(sleep, then_days), 'sleep_n': avg(sleep, now_days), 'stress_t': avg(stress, then_days), 'stress_n': avg(stress, now_days), 'mood_t': avg(mood, then_days), 'mood_n': avg(mood, now_days), 'move_t': avg(move, then_days), 'move_n': avg(move, now_days), 'water_n': avg(water, now_days), 'meals_n': avg(meals, now_days), 'focus_t': avg(focus, then_days), 'focus_n': avg(focus, now_days), 'journal_n': sum((journal.get(d, 0) for d in now_days)), 'grat_n': sum((grat.get(d, 0) for d in now_days)), 'heavy_frac': round(sum((1 for d in mood_now if mood[d] <= 4)) / len(mood_now), 2) if mood_now else None}

def _card(cid, title, obs):
    if not obs:
        return None
    tone, weight, finding, proof, meaning, action = max(obs, key=lambda o: o[1])
    return {'id': cid, 'title': title, 'tone': tone, 'score': weight, 'finding': finding, 'proof': proof, 'meaning': meaning, 'action': action}

def climate(lens='start'):
    from superapp.experience.store import get_recent_memory, load_goals, load_habits
    D = _climate_data(lens)
    links = ['sleep', 'hydration', 'nutrition', 'fitness', 'focus', 'mental', 'habits', 'goals']
    if not D:
        return {'lens': lens, 'span': 0, 'headline': 'The mirror is still gathering you. Live a little; then come back.', 'cards': [], 'steady': [], 'empty': ['Rest & recovery', 'Body & energy', 'Mind & heart', 'Momentum & direction'], 'links': links, 'signals': {'correlations': [], 'patterns': []}}
    A_REST = {'kind': 'habit', 'payload': {'habit_name': 'Wind-down breath', 'completed': False}, 'label': 'start a wind-down habit'}
    A_BODY = {'kind': 'habit', 'payload': {'habit_name': 'A short daily walk', 'completed': False}, 'label': 'start a daily walk'}
    A_MIND = {'kind': 'habit', 'payload': {'habit_name': 'Name one feeling daily', 'completed': False}, 'label': 'start naming feelings'}
    A_MOM = {'kind': 'habit', 'payload': {'habit_name': '25 quiet minutes', 'completed': False}, 'label': 'protect quiet minutes'}
    obs = []
    if D['stress_n'] is not None and D['stress_n'] >= 6:
        obs.append(('attention', 0.9, f"Stress has been a frequent visitor — around {D['stress_n']}/10 lately.", f"stress {D['stress_t']} then → {D['stress_n']} now" if D['stress_t'] is not None else f"stress ~{D['stress_n']}/10 recently", "That's worth knowing, and worth tending. Rest is where it softens first.", A_REST))
    if D['sleep_n'] is not None and D['sleep_n'] < 6.5:
        obs.append(('attention', 0.8, f"Sleep has been running short — about {D['sleep_n']}h.", f"sleep {D['sleep_t']}h then → {D['sleep_n']}h now" if D['sleep_t'] is not None else f"~{D['sleep_n']}h recently", 'Sleep is your keystone; even thirty more minutes changes the day.', A_REST))
    if D['sleep_n'] is not None and D['sleep_n'] >= 7 and (D['sleep_t'] is None or D['sleep_n'] >= D['sleep_t']):
        obs.append(('strength', 0.7, f"You've been sleeping like someone who tends to themselves — {D['sleep_n']}h lately.", f"sleep {D['sleep_t']}h then → {D['sleep_n']}h now" if D['sleep_t'] is not None else f"~{D['sleep_n']}h recently", "Protect this; it's quietly powering everything else.", None))
    rest = _card('rest', 'Rest & recovery', obs)
    obs = []
    if D['move_n'] is not None and D['move_n'] < 10:
        obs.append(('attention', 0.7, 'Movement has been scarce — a few minutes most days.', f"movement {D['move_t']} then → {int(D['move_n'])} min now" if D['move_t'] is not None else 'little movement logged lately', 'Your mood tends to follow your motion. Even a walk counts.', A_BODY))
    elif D['move_n'] is not None and D['move_n'] >= 20:
        obs.append(('strength', 0.7, f"You've been moving regularly — ~{int(D['move_n'])} min on a typical day.", f"movement {D['move_t']} then → {int(D['move_n'])} min now" if D['move_t'] is not None else f"~{int(D['move_n'])} min/day", 'Motion is medicine for you. Keep the rhythm.', None))
    if D['water_n'] is not None and D['water_n'] < 5:
        obs.append(('attention', 0.5, f"Water has been light — around {D['water_n']} glasses a day.", f"~{D['water_n']} glasses/day recently", 'Hydration is the quietest win; the first glass is the kindest.', A_BODY))
    body = _card('body', 'Body & energy', obs)
    obs = []
    if D['heavy_frac'] is not None and D['heavy_frac'] >= 0.5:
        obs.append(('attention', 0.9, f"Heavy feelings have been frequent — {int(D['heavy_frac'] * 100)}% of recent check-ins.", f"mood {D['mood_t']} then → {D['mood_n']} now" if D['mood_t'] is not None else 'recent mood leans heavy', "You may not notice from inside; that's the point of a mirror. It's worth tending, gently.", A_MIND))
    elif D['mood_n'] is not None and D['mood_n'] >= 6.5:
        obs.append(('strength', 0.7, f"Your mood has been bright — around {D['mood_n']}/10.", f"mood {D['mood_t']} then → {D['mood_n']} now" if D['mood_t'] is not None else f"~{D['mood_n']}/10", "Whatever you're doing, it's working. Notice it so you can repeat it.", None))
    if D['grat_n'] >= 3 or D['journal_n'] >= 3:
        obs.append(('strength', 0.5, f"You keep putting feelings into words — {D['journal_n']} journal, {D['grat_n']} gratitude lately.", 'you write things down', "Naming feelings is a practice; you're doing it.", None))
    mind = _card('mind', 'Mind & heart', obs)
    obs = []
    habits = load_habits() or []
    goals = load_goals() or []
    active = [h for h in habits if (h.get('streak') or 0) > 0]
    moving = [g for g in goals if 0 < _num(g.get('progress')) < 100]
    if D['focus_n'] is not None and D['focus_n'] >= 25:
        obs.append(('strength', 0.6, f"You've been protecting quiet — ~{int(D['focus_n'])} min of focus on a typical day.", f"focus {D['focus_t']} then → {int(D['focus_n'])} min now" if D['focus_t'] is not None else f"~{int(D['focus_n'])} min/day", "Protected attention is rare. You're making it.", None))
    if active:
        obs.append(('strength', 0.6, f"You're keeping {len(active)} habit(s) alive right now.", ', '.join((str(h.get('name')) for h in active[:2])), "Consistency is the whole game; you're playing.", None))
    if not active and (not moving) and ((D['focus_n'] or 0) < 10):
        obs.append(('attention', 0.5, 'Momentum has been quiet — no live habits or moving goals right now.', 'no active habits or goals', 'A single small goal would give the days a thread. Want one?', A_MOM))
    mom = _card('momentum', 'Momentum & direction', obs)
    titles = ['Rest & recovery', 'Body & energy', 'Mind & heart', 'Momentum & direction']
    allc = [rest, body, mind, mom]
    cards = sorted([c for c in allc if c and c['score'] >= 0.4], key=lambda c: -c['score'])[:4]
    steady = [t for t, c in zip(titles, allc) if c and c['score'] < 0.4]
    empty = [t for t, c in zip(titles, allc) if c is None]
    m_t, m_n = (D['mood_t'], D['mood_n'])
    if m_t is not None and m_n is not None:
        word = 'rising' if m_n > m_t + 0.4 else 'asking for care' if m_n < m_t - 0.4 else 'steady'
    else:
        word = 'steady'
    scope = 'the last 30 days' if lens == '30' else f"the {D['span']} days since you began"
    return {'lens': lens, 'span': D['span'], 'first': D['first'], 'headline': f'Over {scope}, the shape of you is {word}.', 'cards': cards, 'steady': steady, 'empty': empty, 'links': links, 'signals': _corroboration()}

def _corroboration() -> dict:
    """Independent check from the intelligence layer: upstream Pearson
    correlations over the last 30 days plus pattern-detection insights.
    The cards above are Motif's ranked presentation; these signals are
    the engine room agreeing (or staying silent when data is thin)."""
    try:
        from superapp.experience.store import get_recent_memory
        from superapp.intelligence.patterns import correlations, detect_patterns
        mem = store.get_recent_memory(days=30) or []
        corrs = correlations(mem)
        insights = (detect_patterns().get('insights') or [])[:4]
        return {'correlations': corrs, 'patterns': insights}
    except Exception:
        return {'correlations': [], 'patterns': []}
