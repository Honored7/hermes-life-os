import { motion, useReducedMotion } from 'framer-motion';
import { Wind, Feather, ChatTeardrop, Plus } from '@phosphor-icons/react';
import type { DimConfig, Status } from '../../lib/dimensions';
import { STATUS_COLOR, STATUS_WORD, statusOf } from '../../lib/dimensions';

import { useEffect, useState } from 'react';
function CountUp({ to, decimals = 0 }: { to: number | null; decimals?: number }) {
  const reduce = useReducedMotion();
  const [v, setV] = useState(to ?? 0);
  useEffect(() => {
    if (to == null) { setV(0); return; }
    if (reduce) { setV(to); return; }
    let raf = 0; const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / 650);
      setV(to * (1 - Math.pow(1 - t, 3)));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, reduce]);
  return <>{v.toFixed(decimals)}</>;
}

function Spark({ series, color }: { series: { date: string; value: number }[]; color: string }) {
  const pts = series.slice(-7);
  if (pts.length < 2) return null;
  const W = 100, H = 30, max = Math.max(...pts.map((p) => p.value), 1);
  const min = Math.min(...pts.map((p) => p.value), 0);
  const span = Math.max(0.0001, max - min);
  const xy = pts.map((p, i) => [
    (i / (pts.length - 1)) * W,
    H - ((p.value - min) / span) * (H - 4) - 2,
  ]);
  const d = xy.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-8 w-full">
      <motion.path d={d} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"
        initial={{ pathLength: 0, opacity: 0.2 }} animate={{ pathLength: 1, opacity: 0.9 }}
        transition={{ duration: 0.9, ease: 'easeOut' }} />
    </svg>
  );
}

const ACTION_ICON = { breathe: Wind, journal: Feather, checkin: ChatTeardrop, log: Plus } as const;

export function DimensionCard({
  cfg, data, edge, hero = false, onOpen, onAction,
}: {
  cfg: DimConfig; data: any; edge?: string | null; hero?: boolean;
  onOpen: () => void; onAction: (a: { kind: string; pattern?: 'unwind' | 'box' }) => void;
}) {
  const status: Status = statusOf(cfg, data);
  const sc = STATUS_COLOR[status];
  const value = data?.today ?? data?.latest ?? null;
  const read = cfg.copy[status] + (edge && status !== 'empty' ? ' ' + edge : '');
  const showRecovery = status === 'empty' || status === 'tending';
  const decimals = cfg.valueKey === 'hours' ? 1 : 0;

  return (
    <motion.button
      type="button"
      onClick={onOpen}
      whileHover={{ y: -3 }}
      whileTap={{ scale: 0.985 }}
      transition={{ type: 'spring', stiffness: 300, damping: 24 }}
      className={'group relative overflow-hidden rounded-card border border-line bg-surface p-5 text-left transition-colors hover:border-lantern/30 ' + (hero ? '' : '')}
      style={{ backgroundImage: `radial-gradient(110% 90% at 100% 0%, color-mix(in srgb, ${sc} 12%, transparent), transparent 62%)` }}
    >
      {/* status edge-light */}
      <span className="absolute inset-y-0 left-0 w-1 transition-colors duration-500" style={{ background: sc }} />

      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-full"
            style={{ backgroundColor: `color-mix(in srgb, ${cfg.accent} 14%, transparent)` }}>
            <cfg.icon size={22} weight="light" style={{ color: cfg.accent }} />
          </span>
          <div>
            <p className="text-[10px] uppercase tracking-[0.2em] text-faint">{cfg.label}</p>
            <p className="text-[11px] font-medium" style={{ color: sc }}>{STATUS_WORD[status]}</p>
          </div>
        </div>
        {/* the jaw-dropping headline number */}
        <div className="text-right leading-none">
          <span className="font-wizard text-[34px] text-ink">
            {value != null ? <CountUp to={value} decimals={decimals} /> : '—'}
          </span>
          <span className="ml-1 align-top text-[11px] text-faint">{cfg.unit}</span>
        </div>
      </div>

      {/* the trend */}
      <div className="mt-3 h-8">
        {data?.series?.length >= 2
          ? <Spark series={data.series} color={sc} />
          : <div className="grid h-full place-items-center text-[11px] text-faint/70">the line forms as you log</div>}
      </div>

      {/* the wizard's read */}
      <p className={'mt-3 font-wizard leading-snug text-muted ' + (hero ? 'text-[15px]' : 'text-[13px]')}>
        {read}
      </p>

      {/* recovery — only when the thread needs tending */}
      {showRecovery && (
        <div className="mt-3.5 flex flex-wrap gap-2">
          {cfg.recovery.slice(0, 2).map((a, i) => {
            const Icon = ACTION_ICON[a.kind as keyof typeof ACTION_ICON];
            return (
              <span
                key={i}
                role="button"
                tabIndex={0}
                onClick={(e) => { e.stopPropagation(); onAction(a); }}
                className="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[12px] font-medium transition-all hover:-translate-y-0.5"
                style={{ borderColor: `color-mix(in srgb, ${sc} 45%, var(--line))`, color: sc,
                         backgroundColor: `color-mix(in srgb, ${sc} 9%, transparent)` }}
              >
                <Icon size={14} weight="light" /> {a.label}
              </span>
            );
          })}
        </div>
      )}
    </motion.button>
  );
}
