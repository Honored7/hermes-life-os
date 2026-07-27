import { useEffect, useMemo, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Smiley, Waves, Lightning, Wind, CloudRain, Fire, BatteryLow, HeartHalf } from '@phosphor-icons/react';
import type { IconComponent } from '../icons/dimensions';
import { MotifMark } from '../brand/MotifMark';
import { getMoodWeather } from '../../lib/api';

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
const COLOR: Record<string, string> = Object.fromEntries(MOODS.map((m) => [m.state, m.color]));
const LABEL: Record<string, string> = Object.fromEntries(MOODS.map((m) => [m.state, m.label]));

const R = 88;            // ring radius
const C = 116;           // ring centre (container is 232)
const MOTES = [12, 27, 41, 55, 68, 82, 49];

/** A plain-voice line for the week — deterministic, so it never costs a generation. */
function weatherLine(pred: string | null, temp: number | null, total: number): string {
  if (total < 3) return 'A quiet week so far — its shape is still forming.';
  const base: Record<string, string> = {
    good: 'Brighter days than heavy ones lately.',
    neutral: 'Mostly steady — and that quiet is a kind of strength.',
    stressed: 'Some pressure lately. You have been meeting it.',
    anxious: 'A restless stretch — and you have not been still through it alone.',
    sad: 'A tender, heavier week. Held, not hidden.',
    angry: 'Some heat lately. You let it move instead of swallowing it.',
    low_energy: 'Running on low — and you noticed it, which matters.',
    lonely: 'Some lonely days. Reaching out, even here, counts.',
  };
  let line = (pred && base[pred]) || 'A week of many weathers.';
  if (temp != null && temp >= 7) line += ' The feelings that arrived were strong ones.';
  else if (temp != null && temp <= 3 && (pred === 'good' || pred === 'neutral')) line += ' Gently so.';
  return line;
}

export function MoodAura({ onSelect }: { onSelect?: (state: string) => void }) {
  const reduce = useReducedMotion();
  const [w, setW] = useState<any>(null);
  useEffect(() => { getMoodWeather().then(setW).catch(() => {}); }, []);

  const counts: Record<string, number> = w?.counts || {};
  const total: number = w?.total || 0;
  const maxCount = Math.max(1, ...Object.values(counts));
  const pred: string | null = total ? w.predominant : null;
  const predColor = pred ? COLOR[pred] : 'var(--lantern)';

  const stars = useMemo(
    () =>
      MOODS.map((m, i) => {
        const a = (i / 8) * Math.PI * 2 - Math.PI / 2;
        const n = counts[m.state] || 0;
        const size = 7 + (n / maxCount) * 24;
        const op = total ? 0.28 + 0.72 * (n / maxCount) : 0.22;
        return {
          ...m,
          n,
          size,
          op,
          x: C + R * Math.cos(a),
          y: C + R * Math.sin(a),
          isPred: m.state === pred,
        };
      }),
    [counts, maxCount, total, pred],
  );

  const line = weatherLine(pred, w?.temperature ?? null, total);
  const share = pred && total ? Math.round(((counts[pred] || 0) / total) * 100) : 0;

  return (
    <section className="relative -mx-1 overflow-hidden rounded-card px-1 pb-2 pt-3">
      {/* a single meaningful wash in the colour of the week — not random blobs */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{ background: `radial-gradient(80% 70% at 50% 8%, color-mix(in srgb, ${predColor} 16%, transparent), transparent 70%)` }}
      />
      {/* embers */}
      <div className="pointer-events-none absolute inset-0">
        {MOTES.map((left, i) => (
          <span
            key={i}
            className="absolute bottom-2 h-1 w-1 rounded-full bg-lantern"
            style={{
              left: `${left}%`,
              opacity: reduce ? 0.18 : 0,
              animation: reduce ? undefined : `mote-rise ${7 + (i % 3)}s ease-in ${i * 0.9}s infinite`,
            }}
          />
        ))}
      </div>

      <div className="relative flex flex-col items-center">
        {/* the constellation */}
        <div className="relative" style={{ width: C * 2, height: C * 2 }}>
          <div className="pointer-events-none absolute inset-0 rounded-full border border-line/40"
            style={{ margin: C - R }} />
          {stars.map((s) => (
            <motion.button
              key={s.state}
              type="button"
              onClick={() => onSelect?.(s.state)}
              whileHover={{ scale: 1.18 }}
              whileTap={{ scale: 0.92 }}
              className="absolute grid -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full transition-shadow"
              style={{
                left: s.x,
                top: s.y,
                width: s.size + (s.isPred ? 16 : 8),
                height: s.size + (s.isPred ? 16 : 8),
                backgroundColor: `color-mix(in srgb, ${s.color} ${s.isPred ? 22 : 12}%, transparent)`,
                boxShadow: s.isPred ? `0 0 22px color-mix(in srgb, ${s.color} 45%, transparent)` : 'none',
              }}
              aria-label={`${s.label}: ${s.n} day${s.n === 1 ? '' : 's'}`}
            >
              <s.icon size={Math.max(13, s.size * 0.62)} weight={s.isPred ? 'regular' : 'light'} style={{ color: s.color, opacity: s.op }} />
            </motion.button>
          ))}

          {/* centre: the predominant feeling, or a quiet mark */}
          <div className="absolute left-1/2 top-1/2 grid -translate-x-1/2 -translate-y-1/2 place-items-center text-center">
            {pred ? (
              <>
                <span className="font-wizard text-[22px] leading-none" style={{ color: predColor }}>{LABEL[pred]}</span>
                <span className="mt-1 text-[10px] uppercase tracking-[0.2em] text-faint">{share}% of the week</span>
              </>
            ) : (
              <div className="opacity-70"><MotifMark size={40} /></div>
            )}
          </div>
        </div>

        {/* the voice line */}
        <p className="mt-1 max-w-[18rem] text-center font-wizard text-[16px] leading-snug text-muted">
          {total ? line : 'A quiet page — your week has not left its mark here yet.'}
        </p>
      </div>
    </section>
  );
}
