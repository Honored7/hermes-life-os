import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smiley, Waves, Lightning, Wind, CloudRain, Fire, BatteryLow, HeartHalf,
  CalendarBlank, Check, ArrowSquareOut,
} from '@phosphor-icons/react';
import type { IconComponent } from '../components/icons/dimensions';
import { streamCheckIn, getCalendarEvents, logLife } from '../lib/api';
import { InterventionCard } from '../components/cards/InterventionCard';
import { ProtocolJourney } from '../components/journey/ProtocolJourney';
import { BreathingSession } from '../components/session/BreathingSession';
import { SteadySheet, type SteadyMethod } from '../components/session/SteadySheet';
import { PreparationRitual } from '../components/session/PreparationRitual';
import { MotifMark } from '../components/brand/MotifMark';

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

const STRESS_HINTS = ['presentation', 'deadline', 'interview', 'review', 'demo', 'exam', 'pitch', 'defense', 'defence', 'performance', 'hearing'];
const isStressfulTitle = (t: string) => STRESS_HINTS.some((h) => (t || '').toLowerCase().includes(h));

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

  const accent = mood ? mood.color : 'var(--lantern)';

  // drop anything that has already ended (the cache can lag a few minutes)
  const live = events.filter((e) => new Date(e.end_iso).getTime() > Date.now() - 60000);
  const imminent = live[0] || null;
  const isPrepared = (ev: CalEvent) => !!prepared[prepKey(ev)];
  const minutesTo = imminent ? (new Date(imminent.start_iso).getTime() - Date.now()) / 60000 : Infinity;
  const emphasised = !!imminent && !isPrepared(imminent) && (isStressfulTitle(imminent.title) || minutesTo <= 90);
  const moreUnprepared = imminent ? live.slice(1).filter((e) => !isPrepared(e)).length : 0;

  const hour = new Date().getHours();
  const greeting =
    hour < 5 ? 'It’s late' :
    hour < 12 ? 'Good morning' :
    hour < 17 ? 'Good afternoon' :
    hour < 21 ? 'Good evening' : 'It’s late';

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
    // the reward: the big card steps aside into a quiet line
    if (t === imminent) setCardOpen(false);
  };

  // ── full-screen overlays ──
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

  return (
    <div className="relative h-full overflow-y-auto">
      <motion.div
        className="pointer-events-none absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full blur-[110px]"
        animate={{ backgroundColor: accent, opacity: mood ? 0.22 : 0.1 }}
        transition={{ duration: 0.9 }}
      />

      <div className="relative space-y-6 pb-8 pt-2">
        <div>
          <h1 className="font-wizard text-[28px] leading-tight">{greeting}.</h1>
          <p className="mt-1 text-sm text-muted">How are you arriving right now?</p>
        </div>

        {/* ── the horizon: a stackable, settle-able window onto your day ── */}
        {imminent && (
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
                <span className="absolute inset-y-0 left-0 w-1 transition-colors duration-500"
                  style={{ background: emphasised ? 'var(--lantern)' : isPrepared(imminent) ? 'var(--sage)' : 'var(--line)' }} />
                <div className="pointer-events-none absolute -right-6 -top-8 h-28 w-28 rounded-full bg-lantern/10 blur-2xl" />

                {/* header: mood label + depth chip */}
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-[10px] uppercase tracking-[0.2em] text-faint">
                    {emphasised ? 'coming up — a big one' : 'on your horizon'}
                  </p>
                  {live.length > 1 && (
                    <span className="rounded-full border border-line px-2 py-0.5 text-[10px] font-medium text-faint">
                      {live.length} today
                    </span>
                  )}
                </div>

                {/* the stack — scrolls only when it overflows; the cut row + chip say "more" */}
                <div className="no-scrollbar max-h-[212px] space-y-2 overflow-y-auto overscroll-contain pr-0.5">
                  {live.map((ev, i) => {
                    const top = i === 0;
                    const done = isPrepared(ev);
                    const evEmph = top && emphasised;
                    const mins = (new Date(ev.start_iso).getTime() - Date.now()) / 60000;

                    if (top) {
                      // ── the imminent event, drawn large ──
                      return (
                        <div key={prepKey(ev)} className="rounded-2xl bg-bg/50 p-3.5">
                          <div className="flex items-center gap-3">
                            <span className="relative grid h-9 w-9 shrink-0 place-items-center rounded-full"
                              style={{ backgroundColor: 'color-mix(in srgb, var(--lantern) 12%, transparent)' }}>
                              <CalendarBlank size={18} weight="light" className="text-lantern" />
                              {!done && (
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

                          <button
                            onClick={() => openSteady(ev)}
                            className={
                              'mt-3 flex w-full items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition-all ' +
                              (done
                                ? 'border border-sage/40 text-sage hover:bg-sage/10'
                                : evEmph
                                  ? 'bg-lantern text-bg hover:bg-ember hover:shadow-[0_0_20px_rgba(224,162,58,0.4)]'
                                  : 'border border-line text-muted hover:border-lantern/50 hover:text-lantern')
                            }
                          >
                            {done ? <Check size={16} weight="bold" /> : <Wind size={16} weight="light" />}
                            {done ? 'Centred · centre again' : evEmph ? 'Steady yourself before this' : 'A moment to centre first'}
                          </button>
                        </div>
                      );
                    }

                    // ── compact rows beneath ──
                    return (
                      <motion.div
                        key={prepKey(ev)}
                        whileHover={{ x: 2 }}
                        onClick={() => openSteady(ev)}
                        role="button"
                        tabIndex={0}
                        className="group flex cursor-pointer items-center gap-3 rounded-xl border border-line/70 bg-bg/40 px-3 py-2.5 transition-colors hover:border-lantern/40"
                      >
                        <span className="w-[46px] shrink-0 text-right font-wizard text-[13px] text-faint">
                          {fmtClock(ev.start_iso, ev.all_day)}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-[14px] font-medium leading-tight">{ev.title}</span>
                          {ev.location && <span className="block truncate text-[11px] text-faint">{ev.location}</span>}
                        </span>
                        {done
                          ? <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-sage/15"><Check size={13} weight="bold" className="text-sage" /></span>
                          : <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full text-faint transition-colors group-hover:text-lantern"><Wind size={15} weight="light" /></span>}
                        {ev.html_link && (
                          <a href={ev.html_link} target="_blank" rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="grid h-6 w-6 shrink-0 place-items-center rounded-full text-faint transition-colors hover:text-lantern"
                            aria-label="Open in calendar">
                            <ArrowSquareOut size={15} weight="light" />
                          </a>
                        )}
                        <span className="sr-only">{mins <= 90 && isStressfulTitle(ev.title) ? 'a big one' : ''}</span>
                      </motion.div>
                    );
                  })}
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
                    {moreUnprepared > 0 && (
                      <span className="shrink-0 rounded-full border border-line px-2 py-0.5 text-[10px] font-medium text-faint">
                        +{moreUnprepared} more
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

        {/* ── the check-in heartbeat ── */}
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
