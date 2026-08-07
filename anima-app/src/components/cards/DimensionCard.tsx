import { motion } from 'framer-motion';
import type { DimConfig, Status } from '../../lib/dimensions';
import { STATUS_COLOR, STATUS_WORD } from '../../lib/dimensions';
import type { DimModel } from '../../lib/lifeModel';

function Spark({ series, color }: { series: { date: string; value: number }[]; color: string }) {
  const pts = series.slice(-7);
  if (pts.length < 2) return null;
  const W = 100, H = 30;
  const max = Math.max(...pts.map((p) => p.value), 1);
  const xy = pts.map((p, i) => [(i / (pts.length - 1)) * W, H - (p.value / max) * (H - 4) - 2]);
  const d = xy.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-8 w-full">
      <motion.path d={d} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0.2 }} animate={{ pathLength: 1, opacity: 0.9 }}
        transition={{ duration: 0.9, ease: 'easeOut' }} />
    </svg>
  );
}

function statusOfReal(data: any): Status {
  const today = data?.today;
  const target = data?.target;
  const series = data?.series || [];
  const has = today != null || series.some((s: any) => s.value > 0);
  if (!has) return 'empty';
  if (target == null || today == null) return 'steady';
  const lb = !!data?.lower_better;
  const good = lb ? today <= target : today >= target;
  const bad = lb ? today > target * 1.5 : today < target * 0.6;
  if (good) return 'thriving';
  if (bad) return 'tending';
  return 'steady';
}

export function DimensionCard({
  cfg, model, data, hero = false, onOpen, onAction,
}: {
  cfg: DimConfig; model: DimModel; data: any; hero?: boolean;
  onOpen: () => void; onAction: (a: { kind: string; payload?: any; pattern?: 'unwind' | 'box' }) => void;
}) {
  const status = statusOfReal(data);
  const sc = STATUS_COLOR[status];
  const unit = data?.unit || model.unit;
  const today = data?.today ?? null;
  const series = data?.series || [];
  const hasLine = series.filter((s: any) => s.value > 0).length >= 2;
  const read = cfg.copy[status];
  const isListDim = model.id === 'goals' || model.id === 'habits';
  const quicks = (model.quickLogs || []).slice(0, 2);
  const decimals = unit === 'h' ? 1 : 0;

  return (
    <motion.div
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onOpen(); } }}
      whileHover={{ y: -3 }}
      whileTap={{ scale: 0.985 }}
      transition={{ type: 'spring', stiffness: 300, damping: 24 }}
      className="group relative block w-full min-w-0 cursor-pointer overflow-hidden rounded-card border border-line bg-surface p-5 text-left transition-colors hover:border-lantern/30"
      style={{ backgroundImage: `radial-gradient(110% 90% at 100% 0%, color-mix(in srgb, ${sc} 12%, transparent), transparent 62%)` }}
    >
      <span className="absolute inset-y-0 left-0 w-1 transition-colors duration-500" style={{ background: sc }} />

      <div className="flex min-w-0 items-center gap-3">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full"
          style={{ backgroundColor: `color-mix(in srgb, ${cfg.accent} 14%, transparent)` }}>
          <cfg.icon size={20} weight="light" style={{ color: cfg.accent }} />
        </span>
        <div className="min-w-0">
          <p className="truncate text-[10px] uppercase tracking-[0.18em] text-faint">{cfg.label}</p>
          <p className="truncate text-[11px] font-medium" style={{ color: sc }}>{STATUS_WORD[status]}</p>
        </div>
      </div>

      <div className="mt-3 flex items-end justify-between gap-2">
        <span className={'font-wizard leading-none text-ink ' + (hero ? 'text-[44px]' : 'text-[34px]')}>
          {today != null ? Number(today).toFixed(decimals) : '—'}
        </span>
        <span className="pb-1 text-[11px] text-faint">{unit}</span>
      </div>

      <div className="mt-3 h-8">
        {hasLine ? <Spark series={series} color={sc} /> : (
          <div className="relative grid h-full place-items-center text-[11px] text-faint/70">
            <span className="absolute inset-x-1 bottom-1.5 border-b border-dashed border-line/50" />
            <span className="relative">the line forms as you log</span>
          </div>
        )}
      </div>

      <p className={'mt-3 font-wizard leading-snug text-muted ' + (hero ? 'text-[15px]' : 'text-[13px]')}>{read}</p>

      {isListDim ? (
        <div className="mt-3.5">
          <span className="flex items-center justify-center gap-1.5 rounded-full border px-3 py-1.5 text-[12px] font-medium"
            style={{ borderColor: `color-mix(in srgb, ${sc} 45%, var(--line))`, color: sc, backgroundColor: `color-mix(in srgb, ${sc} 9%, transparent)` }}>
            View & update →
          </span>
        </div>
      ) : (
        quicks.length > 0 ? (
          <div className="mt-3.5 flex flex-wrap gap-2">
            {quicks.map((q, i) => (
              <span key={i} role="button" tabIndex={0}
                onClick={(e) => { e.stopPropagation(); onAction(q); }}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.stopPropagation(); e.preventDefault(); onAction(q); } }}
                className="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[12px] font-medium transition-all hover:-translate-y-0.5"
                style={{ borderColor: `color-mix(in srgb, ${sc} 45%, var(--line))`, color: sc, backgroundColor: `color-mix(in srgb, ${sc} 9%, transparent)` }}>
                {q.label}
              </span>
            ))}
          </div>
        ) : null
      )}
    </motion.div>
  );
}
