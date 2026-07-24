import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';
import { X } from '@phosphor-icons/react';
import { completeIntervention } from '../../lib/api';

interface Props {
  config: any;
  state: string;
  severityBefore: number;
  onClose: () => void;
  /** When provided (journey step), skip the rating and continue the path. */
  onComplete?: () => void;
}

export function BreathingSession({ config, state, severityBefore, onClose, onComplete }: Props) {
  const pattern = config.breathing_pattern;
  const phases = [
    { label: 'Breathe in', seconds: pattern.inhale, scale: 1 },
    { label: 'Hold', seconds: pattern.hold_in, scale: 1 },
    { label: 'Breathe out', seconds: pattern.exhale, scale: 0.55 },
    { label: 'Hold', seconds: pattern.hold_out, scale: 0.55 },
  ].filter((p) => p.seconds > 0);

  const [phaseIdx, setPhaseIdx] = useState(0);
  const [cycle, setCycle] = useState(1);
  const [stage, setStage] = useState<'breathe' | 'rate' | 'reflected' | 'stepDone'>('breathe');
  const [after, setAfter] = useState(5);
  const [checkinMsg, setCheckinMsg] = useState('');
  const [sending, setSending] = useState(false);

  const phase = phases[phaseIdx];

  useEffect(() => {
    if (stage !== 'breathe') return;
    const timer = setTimeout(() => {
      const next = (phaseIdx + 1) % phases.length;
      if (next === 0) {
        if (cycle >= pattern.cycles) {
          setStage(onComplete ? 'stepDone' : 'rate');
          return;
        }
        setCycle((c) => c + 1);
      }
      setPhaseIdx(next);
    }, phase.seconds * 1000);
    return () => clearTimeout(timer);
  }, [phaseIdx, cycle, stage, phases.length, pattern.cycles, phase.seconds, onComplete]);

  const submitRating = async () => {
    setSending(true);
    try {
      const res = await completeIntervention(config.intervention_id, state, severityBefore, after);
      setCheckinMsg(res.wizard_message || 'Well done. Every breath counts.');
    } catch {
      setCheckinMsg('Well done. Every breath counts.');
    } finally {
      setSending(false);
      setStage('reflected');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-bg">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-1/3 h-80 w-80 -translate-x-1/2 -translate-y-1/2 rounded-full bg-lantern/10 blur-[120px]" />
      </div>

      <div className="relative flex items-center justify-between px-5 pt-6">
        <p className="font-wizard text-lg">{config.name}</p>
        <button onClick={onClose} className="rounded-full p-2 text-faint hover:text-lantern" aria-label="Close">
          <X size={20} weight="light" />
        </button>
      </div>

      <div className="relative flex flex-1 flex-col items-center justify-center px-6 pb-12">
        {stage === 'breathe' && (
          <>
            <p className="mb-10 text-xs uppercase tracking-widest text-faint">
              Cycle {cycle} of {pattern.cycles}
            </p>
            <div className="relative grid h-64 w-64 place-items-center">
              <motion.div
                className="absolute inset-0 rounded-full bg-lantern/15 blur-2xl"
                animate={{ scale: phase.scale }}
                transition={{ duration: phase.seconds, ease: 'easeInOut' }}
              />
              <motion.div
                className="grid h-44 w-44 place-items-center rounded-full border border-lantern/40 bg-lantern/10"
                animate={{ scale: phase.scale }}
                transition={{ duration: phase.seconds, ease: 'easeInOut' }}
              >
                <motion.div
                  className="h-20 w-20 rounded-full bg-lantern/70 blur-[1px]"
                  animate={{ scale: phase.scale }}
                  transition={{ duration: phase.seconds, ease: 'easeInOut' }}
                />
              </motion.div>
            </div>
            <motion.p
              key={`${phase.label}-${cycle}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-12 font-wizard text-2xl"
            >
              {phase.label}
            </motion.p>
          </>
        )}

        {stage === 'stepDone' && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm text-center">
            <p className="font-wizard text-2xl">Well done.</p>
            <p className="mt-2 text-sm text-muted">You breathed through {pattern.cycles} full cycles. The path continues.</p>
            <button
              onClick={onComplete}
              className="mt-8 w-full rounded-full bg-lantern py-3 font-medium text-bg transition-all hover:bg-ember hover:shadow-[0_0_22px_rgba(245,184,65,0.4)]"
            >
              Continue the journey
            </button>
          </motion.div>
        )}

        {stage === 'rate' && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm text-center">
            <p className="font-wizard text-2xl">Well done.</p>
            <p className="mt-2 text-sm text-muted">You gave yourself {pattern.cycles} full breaths. How do you feel now?</p>
            <div className="mt-6 flex items-center">
              <span className="text-xs text-faint">1</span>
              <input
                type="range" min={1} max={10} value={after}
                onChange={(e) => setAfter(+e.target.value)}
                className="mood-slider mx-3 flex-1"
                style={{ '--slider-color': 'var(--lantern)', '--slider-fill': `${((after - 1) / 9) * 100}%` } as CSSProperties}
              />
              <span className="text-xs text-faint">10</span>
            </div>
            <p className="mt-2 font-wizard text-lg text-lantern">{after}/10</p>
            <button
              onClick={submitRating}
              disabled={sending}
              className="mt-6 w-full rounded-full bg-lantern py-3 font-medium text-bg transition-all hover:bg-ember disabled:opacity-50"
            >
              {sending ? 'Sharing\u2026' : 'Tell the wizard'}
            </button>
          </motion.div>
        )}

        {stage === 'reflected' && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm text-center">
            <div className="mx-auto grid h-16 w-16 place-items-center">
              <motion.div
                className="h-10 w-10 rounded-full bg-lantern/60 blur-md"
                animate={{ scale: [1, 1.25, 1], opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 3, repeat: Infinity }}
              />
            </div>
            <p className="mt-4 font-wizard text-[17px] leading-relaxed">{checkinMsg}</p>
            <button
              onClick={onClose}
              className="mt-8 rounded-full border border-line px-6 py-2.5 text-sm text-muted transition-colors hover:border-lantern/50 hover:text-lantern"
            >
              Return home
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
