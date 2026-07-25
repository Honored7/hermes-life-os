import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smiley, MoonStars, Drop, Leaf, Barbell, FlowerLotus, Crosshair, CheckCircle, FlagBanner,
} from '@phosphor-icons/react';
import type { IconComponent } from '../components/icons/dimensions';
import { getLifeToday, logLife } from '../lib/api';

interface Dim {
  id: string;
  label: string;
  icon: IconComponent;
  color: string;
  kind: 'checkin' | 'water' | 'sleep' | 'note';
}

const DIMENSIONS: Dim[] = [
  { id: 'mood', label: 'Mood & Energy', icon: Smiley, color: 'var(--mood-joy)', kind: 'checkin' },
  { id: 'sleep', label: 'Sleep', icon: MoonStars, color: 'var(--mood-sad)', kind: 'sleep' },
  { id: 'hydration', label: 'Hydration', icon: Drop, color: 'var(--teal)', kind: 'water' },
  { id: 'nutrition', label: 'Nutrition', icon: Leaf, color: 'var(--sage)', kind: 'note' },
  { id: 'fitness', label: 'Fitness', icon: Barbell, color: 'var(--ember)', kind: 'note' },
  { id: 'mental', label: 'Mental', icon: FlowerLotus, color: 'var(--mood-anxious)', kind: 'note' },
  { id: 'focus', label: 'Focus', icon: Crosshair, color: 'var(--lantern)', kind: 'note' },
  { id: 'habits', label: 'Habits', icon: CheckCircle, color: 'var(--mood-calm)', kind: 'note' },
  { id: 'goals', label: 'Goals', icon: FlagBanner, color: 'var(--mood-lonely)', kind: 'note' },
];

function snapshot(dim: Dim, data: any): string {
  if (!data) return '\u2026';
  if (dim.kind === 'water') return `${data.hydration.today} / ${data.hydration.goal} glasses`;
  if (dim.kind === 'sleep')
    return data.sleep.today
      ? `${data.sleep.today.hours}h \u00b7 ${data.sleep.today.quality}/10`
      : `7-day avg ${data.sleep.avg_7d}h`;
  if (dim.kind === 'checkin') return 'Check in \u2192';
  return data.logged[dim.id] ? 'Logged today \u2713' : 'Tap to log';
}

function ProgressRing({ value, goal, color, size = 96 }: { value: number; goal: number; color: string; size?: number }) {
  const r = (size - 14) / 2;
  const c = 2 * Math.PI * r;
  const progress = Math.min(value / goal, 1);
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="var(--surface-2)" strokeWidth="7" fill="none" />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth="7" fill="none" strokeLinecap="round"
          strokeDasharray={c}
          animate={{ strokeDashoffset: c * (1 - progress) }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </svg>
      <span className="absolute font-wizard text-xl">{value}<span className="text-sm text-faint">/{goal}</span></span>
    </div>
  );
}

function SliderRow({ label, value, onChange, min, max, step, color, suffix }: {
  label: string; value: number; onChange: (v: number) => void;
  min: number; max: number; step: number; color: string; suffix?: string;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm text-muted">{label}</span>
        <span className="font-wizard text-lg" style={{ color }}>{value}{suffix}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(+e.target.value)}
        className="mood-slider"
        style={{ '--slider-color': color, '--slider-fill': `${((value - min) / (max - min)) * 100}%` } as CSSProperties}
      />
    </div>
  );
}

function QuickLogSheet({ dim, data, onClose, onLogged }: {
  dim: Dim; data: any; onClose: () => void; onLogged: (stayOpen: boolean) => void;
}) {
  const [hours, setHours] = useState(7);
  const [quality, setQuality] = useState(7);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (payload: any, stayOpen = false) => {
    setBusy(true);
    try {
      await logLife(payload);
      onLogged(stayOpen);
      if (!stayOpen) onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose} className="fixed inset-0 z-40 bg-black/50"
      />
      <motion.div
        initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }}
        transition={{ type: 'spring', damping: 32, stiffness: 320 }}
        className="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-md rounded-t-3xl border-t border-line bg-surface px-6 pb-9 pt-3"
      >
        <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-line" />
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-full" style={{ backgroundColor: `color-mix(in srgb, ${dim.color} 14%, transparent)` }}>
            <dim.icon size={22} weight="light" style={{ color: dim.color }} />
          </div>
          <h3 className="font-wizard text-xl">{dim.label}</h3>
        </div>

        {dim.kind === 'water' && (
          <div className="mt-6 flex flex-col items-center gap-5">
            <ProgressRing value={data?.hydration.today || 0} goal={data?.hydration.goal || 8} color={dim.color} />
            <p className="text-sm text-muted">How are you doing on water today?</p>
            <div className="flex w-full gap-3">
              <button
                onClick={() => submit({ dimension: 'hydration', glasses: 1 }, true)}
                disabled={busy}
                className="flex-1 rounded-full py-3 font-medium text-bg transition-all disabled:opacity-50"
                style={{ backgroundColor: dim.color }}
              >
                +1 glass
              </button>
              <button
                onClick={() => submit({ dimension: 'hydration', glasses: 2 }, true)}
                disabled={busy}
                className="flex-1 rounded-full border py-3 font-medium transition-all disabled:opacity-50"
                style={{ borderColor: dim.color, color: dim.color }}
              >
                +2 glasses
              </button>
            </div>
          </div>
        )}

        {dim.kind === 'sleep' && (
          <div className="mt-6 space-y-5">
            <SliderRow label="How long did you sleep?" value={hours} onChange={setHours} min={0} max={12} step={0.5} color={dim.color} suffix="h" />
            <SliderRow label="How restful was it?" value={quality} onChange={setQuality} min={1} max={10} step={1} color={dim.color} suffix="/10" />
            <button
              onClick={() => submit({ dimension: 'sleep', hours, quality })}
              disabled={busy}
              className="w-full rounded-full py-3 font-medium text-bg transition-all disabled:opacity-50"
              style={{ backgroundColor: dim.color }}
            >
              {busy ? 'Saving\u2026' : 'Save my night'}
            </button>
          </div>
        )}

        {dim.kind === 'note' && (
          <div className="mt-6 space-y-4">
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder={`What about ${dim.label.toLowerCase()} today?`}
              rows={3}
              className="w-full resize-none rounded-xl border border-line bg-bg px-4 py-3 text-sm outline-none transition-colors placeholder:text-faint focus:border-lantern/60"
            />
            <button
              onClick={() => submit({ dimension: dim.id, note })}
              disabled={busy || !note.trim()}
              className="w-full rounded-full py-3 font-medium text-bg transition-all disabled:opacity-40"
              style={{ backgroundColor: dim.color }}
            >
              Log it
            </button>
          </div>
        )}
      </motion.div>
    </>
  );
}

export function Life({ onCheckIn }: { onCheckIn: () => void }) {
  const [data, setData] = useState<any>(null);
  const [selected, setSelected] = useState<Dim | null>(null);

  const refresh = () => getLifeToday().then(setData).catch(() => {});
  useEffect(() => { refresh(); }, []);

  return (
    <div className="relative h-full overflow-y-auto">
      <div className="pointer-events-none absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-sage blur-[120px] opacity-10" />

      <div className="relative pb-8 pt-2">
        <h1 className="font-wizard text-[28px] leading-tight">Your life</h1>
        <p className="mt-1 text-sm text-muted">Nine dimensions, gently tracked.</p>

        <div className="mt-6 grid grid-cols-2 gap-3">
          {DIMENSIONS.map((dim) => (
            <motion.button
              key={dim.id}
              whileTap={{ scale: 0.97 }}
              onClick={() => (dim.kind === 'checkin' ? onCheckIn() : setSelected(dim))}
              className="flex flex-col items-start gap-3 rounded-card border border-line bg-surface p-4 text-left transition-colors hover:border-lantern/30"
            >
              <div className="grid h-10 w-10 place-items-center rounded-full" style={{ backgroundColor: `color-mix(in srgb, ${dim.color} 14%, transparent)` }}>
                <dim.icon size={22} weight="light" style={{ color: dim.color }} />
              </div>
              <div className="w-full">
                <p className="text-sm font-medium">{dim.label}</p>
                <p className="mt-0.5 text-xs text-faint">{snapshot(dim, data)}</p>
              </div>
              {dim.kind === 'water' && data && (
                <div className="h-1 w-full overflow-hidden rounded-full bg-surface-2">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: dim.color }}
                    animate={{ width: `${Math.min((data.hydration.today / data.hydration.goal) * 100, 100)}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              )}
            </motion.button>
          ))}
        </div>
      </div>

      <AnimatePresence>
        {selected && (
          <QuickLogSheet
            dim={selected}
            data={data}
            onClose={() => setSelected(null)}
            onLogged={(stayOpen) => { refresh(); if (!stayOpen) setSelected(null); }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
