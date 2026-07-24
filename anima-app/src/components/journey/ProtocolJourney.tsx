import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';
import { Check, Wind, Heart, ArrowRight } from '@phosphor-icons/react';
import { BreathingSession } from '../session/BreathingSession';
import { completeIntervention } from '../../lib/api';

const STATE_COLORS: Record<string, string> = {
  angry: 'var(--mood-angry)',
  anxious: 'var(--mood-anxious)',
  overwhelmed: 'var(--mood-stressed)',
  sad: 'var(--mood-sad)',
  low_energy: 'var(--mood-low)',
  lonely: 'var(--mood-lonely)',
};

type StepStatus = 'done' | 'active' | 'todo';

/** Reveals the wizard's words a little at a time, like speech. */
function Spoken({ text }: { text: string }) {
  const words = text.split(' ');
  const [count, setCount] = useState(0);
  useEffect(() => {
    setCount(0);
    const iv = setInterval(() => {
      setCount((c) => {
        if (c >= words.length) { clearInterval(iv); return c; }
        return c + 1;
      });
    }, 45);
    return () => clearInterval(iv);
  }, [text]);
  return (
    <span>
      {words.slice(0, count).join(' ')}
      {count < words.length && (
        <motion.span
          className="ml-1 inline-block h-3.5 w-1 translate-y-0.5 rounded-full bg-lantern"
          animate={{ opacity: [1, 0.2, 1] }}
          transition={{ duration: 0.9, repeat: Infinity }}
        />
      )}
    </span>
  );
}

/** Soft circular countdown for short physical steps (cold water, etc.). */
function StepTimer({ seconds }: { seconds: number }) {
  const [left, setLeft] = useState(seconds);
  useEffect(() => {
    if (left <= 0) return;
    const t = setTimeout(() => setLeft((l) => l - 1), 1000);
    return () => clearTimeout(t);
  }, [left]);
  const r = 26;
  const c = 2 * Math.PI * r;
  const progress = left / seconds;
  return (
    <div className="flex items-center gap-3.5">
      <div className="relative grid h-16 w-16 place-items-center">
        <svg width="64" height="64" className="-rotate-90">
          <circle cx="32" cy="32" r={r} stroke="var(--surface-2)" strokeWidth="4" fill="none" />
          <circle
            cx="32" cy="32" r={r} stroke="var(--lantern)" strokeWidth="4" fill="none"
            strokeDasharray={c} strokeDashoffset={c * (1 - progress)} strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s linear' }}
          />
        </svg>
        <span className="absolute font-wizard text-lg">{left}</span>
      </div>
      <p className="max-w-[180px] text-xs leading-relaxed text-faint">
        {left > 0 ? 'A gentle timer — no rush.' : 'Whenever you\u2019re ready.'}
      </p>
    </div>
  );
}

interface Props {
  protocol: any;
  state: string;
  severityBefore: number;
  onDone: () => void;
}

export function ProtocolJourney({ protocol, state, severityBefore, onDone }: Props) {
  const steps = protocol.steps;
  const accent = STATE_COLORS[protocol.trigger_state] || 'var(--lantern)';

  const [current, setCurrent] = useState(0);
  const [showBreathing, setShowBreathing] = useState(false);
  const [after, setAfter] = useState(5);
  const [reflecting, setReflecting] = useState(false);
  const [closing, setClosing] = useState('');
  const [finished, setFinished] = useState(false);

  const advance = () => setCurrent((c) => Math.min(c + 1, steps.length - 1));

  const submitCheckin = async () => {
    setReflecting(true);
    const firstIv = steps.find((s: any) => s.intervention)?.intervention;
    try {
      const res = await completeIntervention(firstIv?.id ?? 0, state, severityBefore, after);
      setClosing(res.wizard_message || 'You did something real for yourself today.');
    } catch {
      setClosing('You did something real for yourself today.');
    } finally {
      setReflecting(false);
      setFinished(true);
    }
  };

  // ── Breathing step opens the session, then returns to the path ──
  if (showBreathing) {
    const step = steps[current];
    return (
      <BreathingSession
        config={step.session_config}
        state={state}
        severityBefore={severityBefore}
        onComplete={() => { setShowBreathing(false); advance(); }}
        onClose={() => setShowBreathing(false)}
      />
    );
  }

  // ── Journey's end ──
  if (finished) {
    const improved = severityBefore - after;
    return (
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="pt-2 text-center">
        <div className="mx-auto grid h-20 w-20 place-items-center">
          <motion.div
            className="h-12 w-12 rounded-full blur-md"
            style={{ backgroundColor: accent, opacity: 0.6 }}
            animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0.9, 0.5] }}
            transition={{ duration: 3.2, repeat: Infinity }}
          />
        </div>
        <h2 className="mt-2 font-wizard text-2xl">You walked the whole path.</h2>
        <div className="mt-4 flex items-center justify-center gap-3 font-wizard text-xl">
          <span className="text-faint line-through">{severityBefore}</span>
          <ArrowRight size={18} weight="light" className="text-lantern" />
          <span style={{ color: accent }}>{after}</span>
        </div>
        {improved > 0 && (
          <p className="mt-1 text-xs text-faint">That's a real shift — and you did it.</p>
        )}
        <p className="mx-auto mt-5 max-w-xs font-wizard text-[16px] leading-relaxed">{closing}</p>
        <button
          onClick={onDone}
          className="mt-8 rounded-full border border-line px-7 py-2.5 text-sm text-muted transition-colors hover:border-lantern/50 hover:text-lantern"
        >
          Return home
        </button>
      </motion.div>
    );
  }

  return (
    <div className="pt-1">
      {/* Journey header */}
      <div className="mb-1 flex items-baseline justify-between">
        <h2 className="font-wizard text-xl" style={{ color: accent }}>{protocol.name}</h2>
        <span className="text-[11px] uppercase tracking-widest text-faint">
          Step {current + 1} of {steps.length}
        </span>
      </div>
      {/* Progress — the path lights up behind you */}
      <div className="mb-6 h-1 overflow-hidden rounded-full bg-surface-2">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: accent }}
          animate={{ width: `${((current + 1) / steps.length) * 100}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>

      {/* The path */}
      <div>
        {steps.map((step: any, i: number) => {
          const status: StepStatus = i < current ? 'done' : i === current ? 'active' : 'todo';
          const isLast = i === steps.length - 1;
          const isBreathing = !!step.session_config?.breathing_pattern;
          const isCheckin = !!step.is_check_in;
          const shortTimer = !isBreathing && !isCheckin && step.intervention && step.intervention.duration_seconds <= 180;

          return (
            <div key={i} className="flex">
              {/* Node + connecting line */}
              <div className="mr-4 flex flex-col items-center">
                <Node status={status} isCheckin={isCheckin} isBreathing={isBreathing} accent={accent} />
                {!isLast && (
                  <div
                    className="my-1 w-px flex-1 transition-colors duration-700"
                    style={{ backgroundColor: i < current ? accent : 'var(--line)', opacity: i < current ? 0.6 : 1 }}
                  />
                )}
              </div>

              {/* Step content */}
              <div className="min-w-0 flex-1 pb-7">
                {status === 'todo' && (
                  <p className="pt-1.5 text-sm text-faint">{step.intervention_name}</p>
                )}

                {status === 'done' && (
                  <p className="pt-1.5 text-sm text-muted line-through decoration-faint/50">
                    {step.intervention_name}
                  </p>
                )}

                {status === 'active' && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
                    <p className="font-wizard text-lg leading-tight">{step.intervention_name}</p>
                    <p className="mt-2 text-[15px] leading-relaxed text-muted">
                      <Spoken text={step.wizard_message} />
                    </p>

                    {/* Breathing step */}
                    {isBreathing && (
                      <button
                        onClick={() => setShowBreathing(true)}
                        className="mt-4 flex w-full items-center justify-center gap-2 rounded-full bg-lantern py-2.5 font-medium text-bg transition-all hover:bg-ember hover:shadow-[0_0_22px_rgba(245,184,65,0.4)]"
                      >
                        <Wind size={18} weight="light" /> Begin the breathing
                      </button>
                    )}

                    {/* Check-in step */}
                    {isCheckin && (
                      <div className="mt-4 rounded-card border border-line bg-surface p-4">
                        <p className="text-sm text-muted">Where is it now?</p>
                        <div className="mt-3 flex items-center">
                          <span className="text-xs text-faint">1</span>
                          <input
                            type="range" min={1} max={10} value={after}
                            onChange={(e) => setAfter(+e.target.value)}
                            className="mood-slider mx-3 flex-1"
                            style={{ '--slider-color': accent, '--slider-fill': `${((after - 1) / 9) * 100}%` } as CSSProperties}
                          />
                          <span className="text-xs text-faint">10</span>
                        </div>
                        <p className="mt-1.5 text-right font-wizard text-lg" style={{ color: accent }}>{after}/10</p>
                        <button
                          onClick={submitCheckin}
                          disabled={reflecting}
                          className="mt-3 w-full rounded-full py-2.5 font-medium text-bg transition-all disabled:opacity-50"
                          style={{ backgroundColor: accent }}
                        >
                          {reflecting ? 'The wizard is reflecting\u2026' : 'Tell the wizard'}
                        </button>
                      </div>
                    )}

                    {/* Action / reflection step */}
                    {!isBreathing && !isCheckin && step.intervention && (
                      <div className="mt-4 space-y-3">
                        <ul className="space-y-1.5">
                          {step.intervention.steps.slice(0, 4).map((s: string, j: number) => (
                            <li key={j} className="flex gap-2.5 text-sm leading-relaxed text-muted">
                              <span className="mt-0.5 font-wizard" style={{ color: accent }}>{j + 1}.</span>
                              <span>{s}</span>
                            </li>
                          ))}
                        </ul>
                        {shortTimer && <StepTimer seconds={step.intervention.duration_seconds} />}
                        <button
                          onClick={advance}
                          className="w-full rounded-full border py-2.5 text-sm font-medium transition-all hover:shadow-[0_0_18px_rgba(245,184,65,0.25)]"
                          style={{ borderColor: accent, color: accent }}
                        >
                          I did it — continue
                        </button>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Node({ status, isCheckin, isBreathing, accent }: {
  status: StepStatus; isCheckin: boolean; isBreathing: boolean; accent: string;
}) {
  if (status === 'done') {
    return (
      <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full border" style={{ borderColor: accent, backgroundColor: `color-mix(in srgb, ${accent} 15%, transparent)` }}>
        <Check size={15} weight="bold" style={{ color: accent }} />
      </div>
    );
  }
  if (status === 'active') {
    return (
      <div className="relative grid h-8 w-8 shrink-0 place-items-center">
        <motion.span
          className="absolute inset-0 rounded-full blur-md"
          style={{ backgroundColor: accent, opacity: 0.5 }}
          animate={{ scale: [1, 1.35, 1], opacity: [0.35, 0.7, 0.35] }}
          transition={{ duration: 2.4, repeat: Infinity }}
        />
        <span className="relative grid h-8 w-8 place-items-center rounded-full border" style={{ borderColor: accent, backgroundColor: 'var(--bg)' }}>
          {isCheckin
            ? <Heart size={14} weight="fill" style={{ color: accent }} />
            : isBreathing
              ? <Wind size={14} weight="light" style={{ color: accent }} />
              : <span className="h-2 w-2 rounded-full" style={{ backgroundColor: accent }} />}
        </span>
      </div>
    );
  }
  return <div className="h-8 w-8 shrink-0 rounded-full border border-line" />;
}
