import { useState } from 'react';
import type { CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smiley, Waves, Lightning, Wind, CloudRain, Fire, BatteryLow, HeartHalf,
} from '@phosphor-icons/react';
import type { IconComponent } from '../components/icons/dimensions';
import { streamCheckIn } from '../lib/api';
import { InterventionCard } from '../components/cards/InterventionCard';
import { ProtocolJourney } from '../components/journey/ProtocolJourney';
import { BreathingSession } from '../components/session/BreathingSession';
import { LanternLogo } from '../components/brand/LanternLogo';

interface Mood {
  state: string;
  label: string;
  icon: IconComponent;
  color: string;
}

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

type Phase = 'select' | 'listening' | 'responded';

export function Today() {
  const [mood, setMood] = useState<Mood | null>(null);
  const [severity, setSeverity] = useState(5);
  const [note, setNote] = useState('');
  const [phase, setPhase] = useState<Phase>('select');
  const [wizardMsg, setWizardMsg] = useState('');
  const [meta, setMeta] = useState<any>(null);
  const [showSession, setShowSession] = useState(false);

  const accent = mood ? mood.color : 'var(--lantern)';

  const hour = new Date().getHours();
  const greeting =
    hour < 5 ? 'It\u2019s late' :
    hour < 12 ? 'Good morning' :
    hour < 17 ? 'Good afternoon' :
    hour < 21 ? 'Good evening' : 'It\u2019s late';

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
      setWizardMsg('I\u2019m having trouble connecting right now. Try again in a moment?');
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

  // Standalone breathing session (single intervention, full rating flow)
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
                className="w-full rounded-full py-3 font-medium transition-all hover:shadow-[0_0_24px_rgba(245,184,65,0.4)]"
                style={{ background: accent, color: 'var(--bg)' }}
              >
                Share with the wizard
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {(phase === 'listening' || phase === 'responded') && (
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="mt-1 shrink-0">
                <LanternLogo size={26} breathing={phase === 'listening'} />
              </div>
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

            {/* A protocol journey, or a single intervention */}
            {meta?.protocol ? (
              <ProtocolJourney
                protocol={meta.protocol}
                state={mood!.state}
                severityBefore={severity}
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
    </div>
  );
}
