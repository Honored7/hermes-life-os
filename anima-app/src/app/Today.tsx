import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smiley, Waves, Lightning, Wind, CloudRain, Fire, BatteryLow, HeartHalf,
  CalendarBlank, Check, ArrowSquareOut, Sparkle, Heart, SpeakerHigh,
} from '@phosphor-icons/react';
import type { IconComponent } from '../components/icons/dimensions';
import { streamCheckIn, getCalendarEvents, logLife, getTodayBriefing, postLifeLog } from '../lib/api';
import { getTodayAlive } from '../lib/api';
import { fetchWhisper } from '../lib/api';
import { isSpeaking, speak, stopSpeak, supportsSpeech, ensureVoices } from '../lib/speak';
import { openDimension, openTab } from '../lib/navBus';
import { presentation, toneOf } from '../lib/eventTone';
import { InterventionCard } from '../components/cards/InterventionCard';
import { ProtocolJourney } from '../components/journey/ProtocolJourney';
import { BreathingSession } from '../components/session/BreathingSession';
import { SteadySheet, type SteadyMethod } from '../components/session/SteadySheet';
import { PreparationRitual } from '../components/session/PreparationRitual';
import { MotifMark } from '../components/brand/MotifMark';
import { MoodAura } from '../components/cards/MoodAura';

interface Mood { state: string; label: string; icon: IconComponent; color: string; }

const MOODS: Mood[] = [
  { state: 'good', label: 'Joyful', icon: Smiley, color: 'var(--mood-joy)' },
  { state: 'neutral', label: 'Calm', icon: Waves, color: 'var(--mood-calm)' },
  { state: 'stressed', label: 'Stressed', icon: Lightning, color: 'var(--mood-stressed)' },
  { state: 'anxious', label: 'Anxious', icon: Wind, color: 'var(--mood-anxious)' },
  { state: 'sad', label: 'Sad', icon: CloudRain, color: 'var(--mood-sad)' },
  { state: 'angry', label: 'Angry', icon: Fire, color: 'var(--mood-angry)' },
  { state: 'low_energy', label: 'Drained', icon: BatteryLow, color: 'var(--mood-low)' },
  { state: 'lonely', label: 'Lonely', icon: HeartHalf, color: 'var(--mood-lonely)' },
];

const PATTERNS: Record<'unwind' | 'box', any> = {
  unwind: { inhale: 4, hold_in: 2, exhale: 6, hold_out: 0, cycles: 5 },
  box: { inhale: 4, hold_in: 4, exhale: 4, hold_out: 4, cycles: 6 },
};
const PATTERN_LABEL: Record<'unwind' | 'box', string> = { unwind: 'Unwind', box: 'Box breath' };

type Phase = 'select' | 'listening' | 'responded';
type PrepareMode =
  | { kind: 'breath'; method: 'unwind' | 'box'; target: CalEvent }
  | { kind: 'ritual'; target: CalEvent }
  | null;

interface CalEvent {
  id: string;
  provider: string;
  title: string;
  start_iso: string;
  end_iso: string;
  all_day: boolean;
  location: string;
  html_link: string;
}

function fmtClock(iso: string, allDay: boolean): string {
  if (allDay) return 'All day';
  return new Date(iso).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}

// ── "centred" memory, kept for the day so a reload never re-nags ──
const prepKey = (ev: CalEvent) => `${ev.provider}:${ev.id}`;
const todayKey = () => {
  const d = new Date();
  return `motif-prepared-${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
const loadPrepared = (): Record<string, true> => {
  try {
    const a = JSON.parse(localStorage.getItem(todayKey()) || '[]') as string[];
    const o: Record<string, true> = {};
    for (const k of a) o[k] = true;
    return o;
  } catch {
    return {};
  }
};
const savePrepared = (o: Record<string, true>) => {
  try { localStorage.setItem(todayKey(), JSON.stringify(Object.keys(o))); } catch { /* ignore */ }
};

const CTA_LABEL: Record<string, string> = {
  emphasised: 'Steady yourself before this',
  'gentle-stress': "Prepare when you're ready",
  gentle: 'A moment to centre first',
  done: 'Centred · centre again',
};

export function Today() {
  const [mood, setMood] = useState<Mood | null>(null);
  const [severity, setSeverity] = useState(5);
  const [note, setNote] = useState('');
  const [phase, setPhase] = useState<Phase>('select');
  const [wizardMsg, setWizardMsg] = useState('');
  const [meta, setMeta] = useState<any>(null);
  const [showSession, setShowSession] = useState(false);

  const [events, setEvents] = useState<CalEvent[]>([]);
  const [prepared, setPrepared] = useState<Record<string, true>>(() => loadPrepared());
  const [cardOpen, setCardOpen] = useState(true);
  const [steadyTarget, setSteadyTarget] = useState<CalEvent | null>(null);
  const [steadyOpen, setSteadyOpen] = useState(false);
  const [prepareMode, setPrepareMode] = useState<PrepareMode>(null);

  // ── the companion's briefing (greeting, true line, suggestion) ──
  const [briefing, setBriefing] = useState<any>(null);
  useEffect(() => { getTodayBriefing().then(setBriefing).catch(() => {}); }, []);

  // ── ambient whisper: one line from the mirror, never a chat window ──
  const [whisper, setWhisper] = useState<string | null>(null);
  useEffect(() => { fetchWhisper('today').then((w) => setWhisper(w?.text || null)).catch(() => {}); }, []);

  // ── spoken briefing: tap to hear, tap again to stop ──
  const [reading, setReading] = useState(false);
  const [voiceHint, setVoiceHint] = useState<string | null>(null);
  useEffect(() => {
    if (!voiceHint) return;
    const t = setTimeout(() => setVoiceHint(null), 6000);
    return () => clearTimeout(t);
  }, [voiceHint]);
  const readBriefing = async () => {
    if (reading || isSpeaking()) { stopSpeak(); setReading(false); return; }
    // A device with no voice would otherwise fail silently — the exact
    // "dead button" complaint. Ask first, explain honestly if none.
    const count = await ensureVoices().catch(() => 0);
    if (!count) {
      setVoiceHint('This device has no voice installed, so I stay quiet here. A system voice (or Chrome/Edge) wakes it up.');
      return;
    }
    const parts = [greeting + '.', trueLine || '', whisper || '', suggestion && !isEvening ? suggestion.text : '']
      .filter(Boolean).join(' ');
    if (!parts.trim()) return;
    setReading(true);
    speak(parts, () => setReading(false));
  };
  useEffect(() => () => stopSpeak(), []);

  // ── blooming heart for the mood check-in ──
  const [bloomOpen, setBloomOpen] = useState(false);
  const [breathSuggest, setBreathSuggest] = useState(false);
  const [alive, setAlive] = useState<any>(null);
  useEffect(() => { getTodayAlive().then(setAlive).catch(() => {}); }, []);

  // ── today's intentions (local, per-day, gentle) ──
  type Intention = { id: string; text: string; done: boolean };
  const intentKey = () => {
    const d = new Date();
    return `motif.intentions.${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  };
  const [intentions, setIntentions] = useState<Intention[]>(() => {
    try { return JSON.parse(localStorage.getItem(intentKey()) || '[]') as Intention[]; } catch { return []; }
  });
  const [addingIntent, setAddingIntent] = useState(false);
  const [newIntentText, setNewIntentText] = useState('');
  useEffect(() => { try { localStorage.setItem(intentKey(), JSON.stringify(intentions)); } catch {} }, [intentions]);
  const addIntent = () => {
    const t = newIntentText.trim();
    if (!t) return;
    setIntentions((prev) => [...prev, { id: String(Date.now()), text: t, done: false }]);
    setNewIntentText('');
    setAddingIntent(false);
  };
  const toggleIntent = (id: string) => setIntentions((prev) => prev.map((i) => i.id === id ? { ...i, done: !i.done } : i));
  const removeIntent = (id: string) => setIntentions((prev) => prev.filter((i) => i.id !== id));

  const accent = mood ? mood.color : 'var(--lantern)';
  const nowMs = Date.now();

  // drop anything that has already ended (the cache can lag a few minutes)
  const live = events.filter((e) => new Date(e.end_iso).getTime() > nowMs - 60000);
  const imminent = live[0] || null;
  const isPrepared = (ev: CalEvent) => !!prepared[prepKey(ev)];
  const ctaOf = (ev: CalEvent) =>
    presentation({ title: ev.title, startMs: new Date(ev.start_iso).getTime(), nowMs, prepared: isPrepared(ev) });

  const topCta = imminent ? ctaOf(imminent) : 'none';
  const moreAwaiting = imminent
    ? live.slice(1).filter((e) => !isPrepared(e) && toneOf(e.title) !== 'rest').length
    : 0;

  const hour = new Date().getHours();
  const greeting = briefing?.greeting || (
    hour < 5 ? "It's late" :
    hour < 12 ? "Good morning" :
    hour < 17 ? "Good afternoon" :
    hour < 21 ? "Good evening" : "It's late");
  const trueLine = briefing?.true_line;
  const isEvening = !!briefing?.evening || hour >= 18;
  const suggestion = briefing?.suggestion;

  useEffect(() => {
    getCalendarEvents(8).then((d) => setEvents(d?.events || [])).catch(() => {});
  }, []);

  const submit = async () => {
    if (!mood || phase === 'listening') return;
    setPhase('listening');
    setWizardMsg('');
    setMeta(null);
    try {
      await streamCheckIn(
        { state: mood.state, severity, message: note },
        {
          onMeta: setMeta,
          onToken: (t) => setWizardMsg((prev) => prev + t),
          onDone: () => setPhase('responded'),
        },
      );
    } catch {
      setWizardMsg('I’m having trouble connecting right now. Try again in a moment?');
      setPhase('responded');
    }
  };

  const reset = () => {
    setPhase('select');
    setMood(null);
    setNote('');
    setWizardMsg('');
    setMeta(null);
  };

  const openSteady = (ev: CalEvent) => { setSteadyTarget(ev); setSteadyOpen(true); };
  const pickSteady = (m: SteadyMethod) => {
    if (!steadyTarget) return;
    const target = steadyTarget;
    setSteadyOpen(false);
    setPrepareMode(m === 'intention' ? { kind: 'ritual', target } : { kind: 'breath', method: m, target });
  };

  const finishPrepare = (methodLabel: string) => {
    const t = prepareMode?.target;
    setPrepareMode(null);
    if (!t) return;
    const k = prepKey(t);
    setPrepared((p) => {
      const n: Record<string, true> = { ...p };
      n[k] = true;
      savePrepared(n);
      return n;
    });
    logLife({ dimension: 'preparation', note: `${methodLabel} before ${t.title}` }).catch(() => {});
    if (t === imminent) setCardOpen(false);
  };

  // ── full-screen overlays ──
  if (breathSuggest) {
    return (
      <BreathingSession
        config={{ name: 'Unwind', breathing_pattern: PATTERNS.unwind }}
        state="calm"
        severityBefore={0}
        onClose={() => setBreathSuggest(false)}
      />
    );
  }
  if (showSession && meta?.session_config?.breathing_pattern && !meta?.protocol) {
    return (
      <BreathingSession
        config={meta.session_config}
        state={mood!.state}
        severityBefore={severity}
        onClose={() => { setShowSession(false); reset(); }}
      />
    );
  }
  if (prepareMode?.kind === 'breath') {
    const m = prepareMode.method;
    const title = prepareMode.target.title;
    return (
      <BreathingSession
        config={{ name: PATTERN_LABEL[m], breathing_pattern: PATTERNS[m] }}
        state="preparing"
        severityBefore={0}
        onComplete={() => finishPrepare(PATTERN_LABEL[m])}
        onClose={() => setPrepareMode(null)}
        completeHeading="You gave yourself a moment."
        completeBody={`You paused before “${title}”. However small, that steadiness goes with you now.`}
        completeLabel="Carry it with you"
      />
    );
  }
  if (prepareMode?.kind === 'ritual') {
    return (
      <PreparationRitual
        eventTitle={prepareMode.target.title}
        onDone={() => finishPrepare('a moment of intention')}
        onClose={() => setPrepareMode(null)}
      />
    );
  }

  const topEdge =
    topCta === 'emphasised' ? 'var(--lantern)' :
    topCta === 'done' ? 'var(--sage)' :
    topCta === 'rest' ? 'color-mix(in srgb, var(--lantern) 55%, var(--line))' :
    'var(--line)';
  const topLabel =
    topCta === 'emphasised' ? 'coming up — a big one' :
    topCta === 'rest' ? 'yours today' :
    topCta === 'done' ? 'centred' :
    'on your horizon';

  return (
    <div className="relative h-full overflow-y-auto">
      <motion.div
        className="pointer-events-none absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full blur-[110px]"
        animate={{ backgroundColor: accent, opacity: mood ? 0.22 : 0.1 }}
        transition={{ duration: 0.9 }}
      />

      <div className="relative space-y-6 pb-8 pt-2">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-wizard text-[28px] leading-tight">{greeting}.</h1>
            {supportsSpeech() ? (
              <button onClick={readBriefing} aria-label={reading ? 'Stop reading' : 'Hear your briefing'}
                className="grid h-9 w-9 shrink-0 place-items-center rounded-full border transition-all"
                style={{
                  borderColor: reading ? 'var(--lantern)' : 'var(--line)',
                  color: reading ? 'var(--lantern)' : 'var(--faint)',
                  backgroundColor: reading ? 'color-mix(in srgb, var(--lantern) 10%, transparent)' : 'transparent',
                }}>
                <SpeakerHigh size={17} weight="light" />
              </button>
            ) : null}
          </div>
          {voiceHint ? (
            <p className="mt-1.5 text-[12px] italic leading-snug text-muted">{voiceHint}</p>
          ) : null}
          {trueLine ? (
            <p className="mt-1.5 text-[13px] leading-snug text-muted">{trueLine}</p>
          ) : (
            <p className="mt-1 text-sm text-muted">{isEvening ? 'How did the day go?' : 'How are you arriving right now?'}</p>
          )}
          {whisper ? (
            <p className="mt-2 font-wizard text-[13px] italic leading-snug text-muted">“{whisper}”</p>
          ) : null}
          <button onClick={() => openTab('companion')}
            className="mt-2 text-[12px] text-faint underline decoration-dotted underline-offset-4 transition-colors hover:text-lantern">
            sit with me a moment →
          </button>
        </div>

        <MoodAura
          onSelect={(st) => {
            const found = MOODS.find((m) => m.state === st);
            if (found) { setPhase('select'); setWizardMsg(''); setMeta(null); setMood(found); }
          }}
        />

        {/* ── the horizon: tone-aware, stackable, settle-able ── */}
        {(
          <AnimatePresence mode="wait">
            {cardOpen ? (
              <motion.div
                key="active"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8, transition: { duration: 0.25 } }}
                whileHover={{ y: -2 }}
                transition={{ type: 'spring', stiffness: 300, damping: 26 }}
                className="relative overflow-hidden rounded-card border border-line bg-surface p-4"
              >
                <span className="absolute inset-y-0 left-0 w-1 transition-colors duration-500" style={{ background: topEdge }} />
                <div className="pointer-events-none absolute -right-6 -top-8 h-28 w-28 rounded-full bg-lantern/10 blur-2xl" />

                <div className="mb-3 flex items-center justify-between">
                  <p className="text-[10px] uppercase tracking-[0.2em] text-faint">{topLabel}</p>
                  {live.length > 1 && (
                    <span className="rounded-full border border-line px-2 py-0.5 text-[10px] font-medium text-faint">
                      {live.length} today
                    </span>
                  )}
                </div>

                <div className="no-scrollbar max-h-[212px] space-y-2 overflow-y-auto overscroll-contain pr-0.5">
                  {live.map((ev, i) => {
                    const done = isPrepared(ev);
                    const top = i === 0;

                    if (top) {
                      const cta = topCta;
                      const Glyph = cta === 'rest' ? Sparkle : CalendarBlank;
                      const glyphColor = cta === 'rest' || cta === 'done' ? 'var(--sage)' : 'var(--lantern)';
                      const glyphBg = cta === 'rest' || cta === 'done'
                        ? 'color-mix(in srgb, var(--sage) 14%, transparent)'
                        : 'color-mix(in srgb, var(--lantern) 12%, transparent)';
                      const btnClass =
                        cta === 'emphasised'
                          ? 'bg-lantern text-bg hover:bg-ember hover:shadow-[0_0_20px_rgba(224,162,58,0.4)]'
                          : cta === 'done'
                            ? 'border border-sage/40 text-sage hover:bg-sage/10'
                            : 'border border-line text-muted hover:border-lantern/50 hover:text-lantern';
                      const BtnIcon = cta === 'done' ? Check : Wind;

                      return (
                        <div key={prepKey(ev)} className="rounded-2xl bg-bg/50 p-3.5">
                          <div className="flex items-center gap-3">
                            <span className="relative grid h-9 w-9 shrink-0 place-items-center rounded-full" style={{ backgroundColor: glyphBg }}>
                              <Glyph size={18} weight="light" style={{ color: glyphColor }} />
                              {cta === 'emphasised' && (
                                <motion.span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-lantern"
                                  animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 2.2, repeat: Infinity }} />
                              )}
                            </span>
                            <div className="min-w-0 flex-1">
                              <p className="truncate text-[15px] font-medium leading-tight">{ev.title}</p>
                              {ev.location && <p className="truncate text-[11px] text-faint">{ev.location}</p>}
                            </div>
                            <span className="shrink-0 font-wizard text-lg text-muted">{fmtClock(ev.start_iso, ev.all_day)}</span>
                          </div>

                          {cta === 'rest' ? (
                            <div className="mt-3 flex items-center gap-2 rounded-full px-1 py-1 text-[13px] leading-snug text-sage/90">
                              <Sparkle size={15} weight="fill" className="shrink-0 text-sage/80" />
                              <span>No need to brace for this one — it’s here to be enjoyed.</span>
                            </div>
                          ) : cta === 'none' ? null : (
                            <button
                              onClick={() => openSteady(ev)}
                              className={'mt-3 flex w-full items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition-all ' + btnClass}
                            >
                              <BtnIcon size={16} weight={cta === 'done' ? 'bold' : 'light'} />
                              {CTA_LABEL[cta]}
                            </button>
                          )}
                        </div>
                      );
                    }

                    // ── compact rows beneath ──
                    const rowTone = toneOf(ev.title);
                    const canPrepare = rowTone !== 'rest';
                    const RowIcon = done ? Check : rowTone === 'rest' ? Sparkle : Wind;
                    const rowIconColor = done || rowTone === 'rest' ? 'var(--sage)' : 'var(--faint)';

                    return (
                      <motion.div
                        key={prepKey(ev)}
                        whileHover={canPrepare ? { x: 2 } : undefined}
                        onClick={canPrepare ? () => openSteady(ev) : undefined}
                        role={canPrepare ? 'button' : undefined}
                        tabIndex={canPrepare ? 0 : undefined}
                        className={
                          'group flex items-center gap-3 rounded-xl border px-3 py-2.5 transition-colors ' +
                          (canPrepare ? 'cursor-pointer hover:border-lantern/40 ' : '') +
                          (rowTone === 'rest' ? 'border-sage/25' : 'border-line/70 bg-bg/40')
                        }
                        style={rowTone === 'rest'
                          ? { background: 'color-mix(in srgb, var(--sage) 7%, transparent)' }
                          : undefined}
                      >
                        <span className="w-[46px] shrink-0 text-right font-wizard text-[13px] text-faint">
                          {fmtClock(ev.start_iso, ev.all_day)}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-[14px] font-medium leading-tight">{ev.title}</span>
                          {ev.location && <span className="block truncate text-[11px] text-faint">{ev.location}</span>}
                        </span>
                        <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full"
                          style={done || rowTone === 'rest' ? { backgroundColor: 'color-mix(in srgb, var(--sage) 14%, transparent)' } : undefined}>
                          <RowIcon size={done ? 13 : 15} weight={done ? 'bold' : rowTone === 'rest' ? 'fill' : 'light'} style={{ color: rowIconColor }} />
                        </span>
                        {ev.html_link && (
                          <a href={ev.html_link} target="_blank" rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="grid h-6 w-6 shrink-0 place-items-center rounded-full text-faint transition-colors hover:text-lantern"
                            aria-label="Open in calendar">
                            <ArrowSquareOut size={15} weight="light" />
                          </a>
                        )}
                      </motion.div>
                    );
                  })}
                </div>

                {/* ── your intentions (local, today-only) ── */}
                <div className="mt-3 border-t border-line/50 pt-3">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-[10px] uppercase tracking-[0.2em] text-faint">your intentions</p>
                    <button onClick={() => setAddingIntent(true)}
                      className="flex items-center gap-1 text-[11px] text-faint transition-colors hover:text-lantern">
                      <span className="grid h-4 w-4 place-items-center rounded-full bg-lantern/15">
                        <span className="text-[10px] text-lantern">+</span>
                      </span>
                      add
                    </button>
                  </div>
                  {intentions.length === 0 && !addingIntent && (
                    <p className="text-[11px] text-faint">nothing yet — a small list for today only.</p>
                  )}
                  <div className="space-y-1">
                    {intentions.map((i) => (
                      <div key={i.id} className="flex items-center gap-2 rounded-lg px-2 py-1.5 transition-colors hover:bg-bg/40">
                        <button onClick={() => toggleIntent(i.id)}
                          className="grid h-5 w-5 shrink-0 place-items-center rounded-full border transition-all"
                          style={{ borderColor: i.done ? 'var(--sage)' : 'var(--line)', background: i.done ? 'var(--sage)' : 'transparent' }}>
                          {i.done && <Check size={11} weight="bold" style={{ color: 'var(--bg)' }} />}
                        </button>
                        <span className="min-w-0 flex-1 truncate text-[13px]"
                          style={{ color: i.done ? 'var(--faint)' : 'var(--ink)', textDecoration: i.done ? 'line-through' : 'none' }}>
                          {i.text}
                        </span>
                        <button onClick={() => removeIntent(i.id)} className="text-faint transition-colors hover:text-mood-angry">×</button>
                      </div>
                    ))}
                    {addingIntent && (
                      <div className="flex items-center gap-2 rounded-lg bg-bg/40 px-2 py-1.5">
                        <input value={newIntentText} onChange={(e) => setNewIntentText(e.target.value)}
                          onKeyDown={(e) => { if (e.key === 'Enter') addIntent(); if (e.key === 'Escape') { setAddingIntent(false); setNewIntentText(''); } }}
                          autoFocus placeholder="what's on your mind today?"
                          className="min-w-0 flex-1 bg-transparent text-[13px] text-ink outline-none placeholder:text-faint" />
                        <button onClick={addIntent} className="text-[11px] text-lantern">add</button>
                        <button onClick={() => { setAddingIntent(false); setNewIntentText(''); }} className="text-[11px] text-faint">×</button>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ) : (
              // ── settled: the card steps aside into one quiet line ──
              <motion.div
                key="settled"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.35, ease: 'easeOut' }}
                className="overflow-hidden rounded-card border border-sage/30 bg-surface"
              >
                <div className="flex items-center gap-3 p-3.5">
                  <button onClick={() => setCardOpen(true)} className="flex min-w-0 flex-1 items-center gap-3 text-left">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-sage/15">
                      <Check size={15} weight="bold" className="text-sage" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-[10px] uppercase tracking-[0.2em] text-sage/80">centred</span>
                      <span className="block truncate text-[14px] font-medium leading-tight">
                        {imminent.title} · {fmtClock(imminent.start_iso, imminent.all_day)}
                      </span>
                    </span>
                    {moreAwaiting > 0 && (
                      <span className="shrink-0 rounded-full border border-line px-2 py-0.5 text-[10px] font-medium text-faint">
                        +{moreAwaiting} more
                      </span>
                    )}
                  </button>
                  <button onClick={() => openSteady(imminent)}
                    className="shrink-0 rounded-full border border-line px-3 py-1.5 text-[11px] text-muted transition-colors hover:border-sage/50 hover:text-sage">
                    again
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        )}

        {/* ── what's alive today: habits, goals, movement ── */}
        {alive && (alive.habits.length > 0 || alive.goals.length > 0 || alive.move_min > 0) && (
          <div className="rounded-card border border-line bg-surface p-4">
            <p className="text-[10px] uppercase tracking-[0.2em] text-faint">what's alive today</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {alive.habits.map((h: string) => (
                <button key={h} onClick={() => openDimension('habits')}
                  className="rounded-full border border-line px-3 py-1.5 text-[11px] text-muted transition-all hover:border-sage/50 hover:text-sage">
                  {h}
                </button>
              ))}
              {alive.goals.map((g: any) => (
                <button key={g.name} onClick={() => openDimension('goals')}
                  className="rounded-full border border-line px-3 py-1.5 text-[11px] text-muted transition-all hover:border-lantern/50 hover:text-lantern">
                  {g.name} · {g.progress}%
                </button>
              ))}
              {alive.move_min > 0 && (
                <button onClick={() => openDimension('fitness')}
                  className="rounded-full border border-line px-3 py-1.5 text-[11px] text-muted transition-all hover:border-ember/50 hover:text-ember">
                  {alive.move_min} min moved
                </button>
              )}
            </div>
          </div>
        )}

        {/* ── the companion's gentle suggestion ── */}
        {suggestion && !isEvening && (
          <button onClick={() => {
            if (suggestion.kind === 'breathe') setBreathSuggest(true);
            else postLifeLog(suggestion.kind, suggestion.payload || {}).catch(() => {});
          }}
            className="flex w-full items-center gap-3 rounded-card border border-dashed border-lantern/30 bg-surface/50 px-4 py-3 text-left transition-all hover:-translate-y-0.5 hover:border-lantern/60">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-lantern/10">
              <Sparkle size={16} weight="light" style={{ color: 'var(--lantern)' }} />
            </span>
            <span className="min-w-0 flex-1">
              <p className="text-[10px] uppercase tracking-[0.2em] text-faint">a gentle suggestion</p>
              <p className="font-wizard text-[14px] leading-snug text-ink">{suggestion.text}</p>
            </span>
            <span className="shrink-0 text-[11px] text-faint">tap</span>
          </button>
        )}

        {isEvening && (
          <div className="rounded-card border border-sage/30 bg-surface p-4">
            <p className="text-[10px] uppercase tracking-[0.2em] text-faint">the day is closing</p>
            <p className="mt-1 font-wizard text-[15px] leading-snug text-muted">
              How did it go? Tap the heart to name how you feel, and let it settle.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button onClick={() => setBreathSuggest(true)}
                className="rounded-full border border-sage/40 px-3.5 py-1.5 text-[11px] text-sage transition-all hover:bg-sage/10">
                a moment of stillness
              </button>
              <button onClick={() => openTab('life')}
                className="rounded-full border border-line px-3.5 py-1.5 text-[11px] text-muted transition-all hover:border-lantern/50 hover:text-lantern">
                write the day down
              </button>
            </div>
          </div>
        )}

        {/* ── the check-in heartbeat: blooming heart ── */}
        {!bloomOpen && !mood ? (
          <button onClick={() => setBloomOpen(true)}
            className="group flex w-full items-center justify-between rounded-card border border-line bg-surface px-4 py-3.5 transition-all hover:-translate-y-0.5 hover:border-lantern/40">
            <span className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-full"
                style={{ background: 'color-mix(in srgb, var(--lantern) 14%, transparent)' }}>
                <Heart size={20} weight="light" style={{ color: 'var(--lantern)' }} />
              </span>
              <span className="text-left">
                <p className="text-[10px] uppercase tracking-[0.2em] text-faint">{isEvening ? 'how did it go?' : 'how are you?'}</p>
                <p className="text-[14px] font-medium text-ink">tap to check in</p>
              </span>
            </span>
            <span className="text-faint transition-colors group-hover:text-lantern">→</span>
          </button>
        ) : (
          <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
            className="space-y-3">
            <div className="grid grid-cols-4 gap-2.5">
              {MOODS.map((m) => {
                const selected = mood?.state === m.state;
                return (
                  <button
                    key={m.state}
                    onClick={() => {
                      if (phase !== 'select') { setPhase('select'); setWizardMsg(''); setMeta(null); }
                      setMood(m);
                    }}
                    className="flex flex-col items-center gap-2 rounded-xl border py-3.5 transition-all duration-300"
                    style={{
                      borderColor: selected ? m.color : 'var(--line)',
                      background: selected ? `color-mix(in srgb, ${m.color} 13%, transparent)` : 'var(--surface)',
                      boxShadow: selected ? `0 0 18px color-mix(in srgb, ${m.color} 25%, transparent)` : 'none',
                    }}
                  >
                    <m.icon size={26} weight="light" style={{ color: selected ? m.color : 'var(--faint)' }} />
                    <span className="text-[11px] font-medium" style={{ color: selected ? m.color : 'var(--muted)' }}>
                      {m.label}
                    </span>
                  </button>
                );
              })}
            </div>
            {!mood && (
              <button onClick={() => setBloomOpen(false)} className="mx-auto block text-[11px] text-faint hover:text-lantern">
                not now
              </button>
            )}
          </motion.div>
        )}

        <AnimatePresence>
          {mood && phase === 'select' && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="space-y-5"
            >
              <div>
                <div className="mb-2.5 flex items-center justify-between">
                  <span className="text-sm text-muted">How intense?</span>
                  <span className="font-wizard text-lg" style={{ color: accent }}>{severity}/10</span>
                </div>
                <input
                  type="range" min={1} max={10} value={severity}
                  onChange={(e) => setSeverity(+e.target.value)}
                  className="mood-slider"
                  style={{ '--slider-color': accent, '--slider-fill': `${((severity - 1) / 9) * 100}%` } as CSSProperties}
                />
              </div>

              <input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Want to say more? (optional)"
                className="w-full rounded-xl border border-line bg-surface px-4 py-3 text-sm outline-none transition-colors placeholder:text-faint focus:border-lantern/60"
              />

              <button
                onClick={submit}
                className="w-full rounded-full py-3 font-medium transition-all hover:shadow-[0_0_24px_rgba(224,162,58,0.4)]"
                style={{ background: accent, color: 'var(--bg)' }}
              >
                Share with the wizard
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {(phase === 'listening' || phase === 'responded') && (
          <div className="space-y-4">
            {!meta?.protocol && (
              <div className="flex gap-3">
                <div className="mt-1 shrink-0"><MotifMark size={26} /></div>
                <div className="min-w-0">
                  {phase === 'listening' && !wizardMsg ? (
                    <div className="flex items-center gap-1.5 pt-2">
                      {[0, 1, 2].map((i) => (
                        <motion.span
                          key={i}
                          className="h-1.5 w-1.5 rounded-full bg-lantern"
                          animate={{ opacity: [0.25, 1, 0.25] }}
                          transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="font-wizard text-[17px] leading-relaxed">
                      {wizardMsg}
                      {phase === 'listening' && (
                        <motion.span
                          className="ml-1 inline-block h-4 w-1.5 translate-y-0.5 rounded-full bg-lantern"
                          animate={{ opacity: [1, 0.2, 1] }}
                          transition={{ duration: 1, repeat: Infinity }}
                        />
                      )}
                    </p>
                  )}
                </div>
              </div>
            )}

            {meta?.protocol ? (
              <ProtocolJourney
                protocol={meta.protocol}
                state={mood!.state}
                severityBefore={severity}
                userNote={note}
                onDone={reset}
              />
            ) : meta?.intervention ? (
              <InterventionCard
                intervention={meta.intervention}
                sessionConfig={meta.session_config}
                onBegin={() => setShowSession(true)}
              />
            ) : null}

            {phase === 'responded' && !meta?.protocol && (
              <button onClick={reset} className="mx-auto block text-xs text-faint underline-offset-4 hover:text-lantern hover:underline">
                Check in again
              </button>
            )}
          </div>
        )}
      </div>

      <AnimatePresence>
        {steadyOpen && steadyTarget && (
          <SteadySheet
            eventTitle={steadyTarget.title}
            onPick={pickSteady}
            onClose={() => setSteadyOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
