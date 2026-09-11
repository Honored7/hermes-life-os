import { useEffect, useId, useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { MotifMark } from '../brand/MotifMark';

const COLOR: Record<string, string> = {
  good: 'var(--mood-joy)', neutral: 'var(--mood-calm)', stressed: 'var(--mood-stressed)',
  anxious: 'var(--mood-anxious)', sad: 'var(--mood-sad)', angry: 'var(--mood-angry)',
  low_energy: 'var(--mood-low)', lonely: 'var(--mood-lonely)',
};
const WORD: Record<string, string> = {
  good: 'joyful', neutral: 'calm', stressed: 'stressed', anxious: 'anxious',
  sad: 'sad', angry: 'angry', low_energy: 'drained', lonely: 'lonely',
};
const DIR: Record<string, { word: string; color: string }> = {
  warmer: { word: 'warming', color: 'var(--sage)' },
  cooler: { word: 'cooling', color: 'var(--ember)' },
  holding: { word: 'holding', color: 'var(--lantern)' },
  none: { word: 'clearing', color: 'var(--faint)' },
};

const W = 320, H = 124, PAD = 14;
const yOf = (sev: number) => PAD + (1 - (Math.min(Math.max(sev, 1), 10) - 1) / 9) * (H - 2 * PAD);
const wd = (d: string) => new Date(d + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'short' });

export function MoodMirror() {
  const reduce = useReducedMotion();
  const uid = useId().replace(/[:]/g, '');
  const [t, setT] = useState<any>(null);
  const [hover, setHover] = useState<number | null>(null);
  useEffect(() => { getMoodTrendSafe().then(setT).catch(() => {}); }, []);

  const series: { date: string; severity: number; state: string }[] = t?.series || [];
  const n = series.length;
  const xOf = (i: number) => (n > 1 ? (i / (n - 1)) * W : W / 2);
  const pts = series.map((p, i) => [xOf(i), yOf(p.severity)] as const);
  const line = pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ');
  const area = pts.length
    ? `${line} L${W} ${H} L0 ${H} Z`
    : '';

  const dir = DIR[t?.direction] || DIR.none;
  const predColor = t?.this_predominant ? COLOR[t.this_predominant] : 'var(--lantern)';

  return (
    <div
      className="relative overflow-hidden rounded-card border border-line bg-surface p-5 transition-colors hover:border-lantern/30"
      style={{ backgroundImage: `radial-gradient(120% 80% at 0% 0%, color-mix(in srgb, ${predColor} 12%, transparent), transparent 60%)` }}
    >
      {/* header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-faint">your emotional weather</p>
          <p className="font-wizard text-lg leading-tight">The shape of your days</p>
        </div>
        <span className="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium"
          style={{ color: dir.color, backgroundColor: `color-mix(in srgb, ${dir.color} 14%, transparent)` }}>
          {dir.word}
        </span>
      </div>

      {/* the verdict — the big voice of the mirror */}
      <motion.p key={t?.verdict || 'x'} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }}
        className="mt-3 font-wizard text-[18px] leading-snug text-ink">
        {t?.verdict || 'The mirror is gathering your days.'}
      </motion.p>

      {/* the line */}
      <div className="relative mt-5">
        {n === 0 ? (
          <div className="grid h-[124px] place-items-center">
            <div className="flex flex-col items-center gap-2 opacity-70">
              <MotifMark size={34} />
              <p className="text-[12px] text-faint">a few more check-ins and your line appears</p>
            </div>
          </div>
        ) : (
          <>
            <span className="pointer-events-none absolute right-0 top-0 text-[9px] uppercase tracking-wider text-faint/60">intense</span>
            <span className="pointer-events-none absolute bottom-0 right-0 text-[9px] uppercase tracking-wider text-faint/60">gentle</span>
            <div className="relative" style={{ height: H }}
              onMouseLeave={() => setHover(null)} onTouchEnd={() => setHover(null)}>
              <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-full w-full overflow-visible">
                <defs>
                  <linearGradient id={`ma-${uid}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={predColor} stopOpacity="0.28" />
                    <stop offset="100%" stopColor={predColor} stopOpacity="0" />
                  </linearGradient>
                </defs>
                {area && (
                  <motion.path d={area} fill={`url(#ma-${uid})`}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8, delay: 0.3 }} />
                )}
                {line && (
                  <motion.path d={line} fill="none" stroke="var(--ink)" strokeOpacity="0.55"
                    strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"
                    initial={reduce ? false : { pathLength: 0 }} animate={{ pathLength: 1 }}
                    transition={{ duration: 1.1, ease: 'easeOut' }} />
                )}
                {pts.map(([x, y], i) => (
                  <motion.circle key={i} cx={x} cy={y}
                    r={hover === i ? 5.5 : 3.4}
                    fill={COLOR[series[i].state] || 'var(--lantern)'}
                    stroke="var(--bg)" strokeWidth={hover === i ? 2 : 1.2}
                    initial={reduce ? false : { scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2 + i * 0.04, type: 'spring', stiffness: 300, damping: 20 }}
                    style={{ cursor: 'pointer' }}
                    onMouseEnter={() => setHover(i)}
                    onTouchStart={() => setHover(i)}
                  />
                ))}
              </svg>

              {/* the read-out chip */}
              <AnimatePresence>
                {hover != null && series[hover] && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                    className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-lg border border-line bg-bg px-2.5 py-1 text-[11px] shadow-lg"
                    style={{ left: `${(xOf(hover) / W) * 100}%`, top: `${(yOf(series[hover].severity) / H) * 100}%` }}
                  >
                    <span className="text-faint">{wd(series[hover].date)}</span>
                    <span className="mx-1.5" style={{ color: COLOR[series[hover].state] }}>{WORD[series[hover].state]}</span>
                    <span className="font-wizard text-ink">{series[hover].severity}/10</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* x labels: first, mid, last */}
            <div className="mt-1.5 flex justify-between text-[10px] text-faint">
              <span>{wd(series[0].date)}</span>
              {n > 2 && <span>{wd(series[Math.floor(n / 2)].date)}</span>}
              {n > 1 && <span>{wd(series[n - 1].date)}</span>}
            </div>
          </>
        )}
      </div>

      {/* the tone-shift, made visible: last week -> this week */}
      {t && t.this_count > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2 border-t border-line/60 pt-3.5 text-[12px]">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: t.last_predominant ? COLOR[t.last_predominant] : 'var(--faint)' }} />
            <span className="text-faint">last week · {t.last_predominant ? WORD[t.last_predominant] : '—'}</span>
          </span>
          <span className="text-faint/60">→</span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: t.this_predominant ? COLOR[t.this_predominant] : 'var(--faint)' }} />
            <span className="text-muted">this week · {t.this_predominant ? WORD[t.this_predominant] : '—'}</span>
          </span>
          {t.this_intensity != null && (
            <span className="ml-auto text-faint">felt at <span className="font-wizard text-muted">{t.this_intensity}/10</span></span>
          )}
        </div>
      )}
    </div>
  );
}

async function getMoodTrendSafe() {
  const { getMoodTrend } = await import('../../lib/api');
  return getMoodTrend();
}
