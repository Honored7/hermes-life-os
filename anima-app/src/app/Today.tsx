import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smiley, Waves, Lightning, Wind, CloudRain, Fire, BatteryLow, HeartHalf,
  CalendarBlank,
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
  | { kind: 'breath'; method: 'unwind' | 'box' }
  | { kind: 'ritual' }
  | null;

interface CalEvent { id: string; provider: string; title: string; start_iso: string; all_day: boolean; }

function fmtClock(iso: string, allDay: boolean): string {
  if (allDay) return 'All day';
  return new Date(iso).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}

export function Today() {
  const [mood, setMood] = useState<Mood | null>(null);
  const [severity, setSeverity] = useState(5);
  const [note, setNote] = useState('');
  const [phase, setPhase] = useState<Phase>('select');
  const [wizardMsg, setWizardMsg] = useState('');
  const [meta, setMeta] = useState<any>(null);
  const [showSession, setShowSession] = useState(false);

  const [events, setEvents] = useState<CalEvent[]>([]);
  const [steadyOpen, setSteadyOpen] = useState(false);
  const [prepareMode, setPrepareMode] = useState<PrepareMode>(null);

  const accent = mood ? mood.color : 'var(--lantern)';
  const imminent = events[0] || null;
  const minutesTo = imminent ? (new Date(imminent.start_iso).getTime() - Date.now()) / 60000 : Infinity;
  const emphasised = !!imminent && (isStressfulTitle(imminent.title) || minutesTo <= 90);

  const hour = new Date().getHours();
  const greeting =
    hour < 5 ? 'It’s late' :
    hour < 12 ? 'Good morning' :
    hour < 17 ? 'Good afternoon' :
    hour < 21 ? 'Good evening' : 'It’s late';

  useEffect(() => {
    getCalendarEvents(3).then((d) => setEvents(d?.events || [])).catch(() => {});
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

  const pickSteady = (m: SteadyMethod) => {
    setSteadyOpen(false);
    setPrepareMode(m === 'intention' ? { kind: 'ritual' } : { kind: 'breath', method: m });
  };

  const finishPrepare = (methodLabel: string) => {
    const title = imminent?.title || "what's ahead";
    logLife({ dimension: 'preparation', note: `${methodLabel} before ${title}` }).catch(() => {});
    setPrepareMode(null);
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
    return (
      <BreathingSession
        config={{ name: PATTERN_LABEL[m], breathing_pattern: PATTERNS[m] }}
        state="preparing"
        severityBefore={0}
        onComplete={() => finishPrepare(PATTERN_LABEL[m])}
        onClose={() => setPrepareMode(null)}
        completeHeading="You gave yourself a moment."
        completeBody="However small, that pause matters. Carry its calm in with you."
        completeLabel="Carry it with you"
      />
    );
  }
  if (prepareMode?.kind === 'ritual') {
    return (
      <PreparationRitual
        eventTitle={imminent?.title || "what's ahead"}
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

        {/* ── the horizon: what's coming, and a way to steady yourself ── */}
        {imminent && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -2 }}
            transition={{ type: 'spring', stiffness: 300, damping: 26 }}
            className="relative overflow-hidden rounded-card border border-line bg-surface p-4"
          >
            <span className="absolute inset-y-0 left-0 w-1" style={{ background: emphasised ? 'var(--lantern)' : 'var(--line)' }} />
            <div className="pointer-events-none absolute -right-6 -top-8 h-28 w-28 rounded-full bg-lantern/10 blur-2xl" />

            <div className="flex items-center gap-3">
              <span className="relative grid h-9 w-9 shrink-0 place-items-center rounded-full"
                style={{ backgroundColor: 'color-mix(in srgb, var(--lantern) 12%, transparent)' }}>
                <CalendarBlank size={18} weight="light" className="text-lantern" />
                <motion.span
                  className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-lantern"
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 2.2, repeat: Infinity }}
                />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-[10px] uppercase tracking-[0.2em] text-faint">
                  {emphasised ? 'coming up — a big one' : 'on your horizon'}
                </p>
                <p className="truncate text-[15px] font-medium leading-tight">{imminent.title}</p>
              </div>
              <span className="shrink-0 font-wizard text-lg text-muted">{fmtClock(imminent.start_iso, imminent.all_day)}</span>
            </div>

            <button
              onClick={() => setSteadyOpen(true)}
              className={
                'mt-3.5 flex w-full items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition-all ' +
                (emphasised
                  ? 'bg-lantern text-bg hover:bg-ember hover:shadow-[0_0_20px_rgba(224,162,58,0.4)]'
                  : 'border border-line text-muted hover:border-lantern/50 hover:text-lantern')
              }
            >
              <Wind size={16} weight="light" />
              {emphasised ? 'Steady yourself before this' : 'A moment to centre first'}
            </button>
          </motion.div>
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
        {steadyOpen && imminent && (
          <SteadySheet
            eventTitle={imminent.title}
            onPick={pickSteady}
            onClose={() => setSteadyOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
