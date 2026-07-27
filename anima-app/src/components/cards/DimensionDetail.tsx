import { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Wind, Feather, ChatTeardrop, Plus, Link as LinkIcon } from '@phosphor-icons/react';
import type { DimConfig, Status } from '../../lib/dimensions';
import { STATUS_COLOR, STATUS_WORD, statusOf } from '../../lib/dimensions';
import { logLife } from '../../lib/api';

const ACTION_ICON = { breathe: Wind, journal: Feather, checkin: ChatTeardrop, log: Plus } as const;

export function DimensionDetail({
  cfg, data, edge, onClose, onAction, onChanged,
}: {
  cfg: DimConfig; data: any; edge?: string | null;
  onClose: () => void; onAction: (a: { kind: string; pattern?: 'unwind' | 'box' }) => void;
  onChanged: () => void;
}) {
  const status: Status = statusOf(cfg, data);
  const sc = STATUS_COLOR[status];
  const [val, setVal] = useState<string>('');
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const bars = (data?.series || []).slice(-14);
  const max = Math.max(1, ...bars.map((b: any) => b.value));

  const save = async () => {
    if (!cfg.valueKey || val === '') return;
    setSaving(true);
    try {
      await logLife({ dimension: cfg.id, [cfg.valueKey]: Number(val), note: note || undefined } as any);
      setVal(''); setNote(''); onChanged();
    } finally { setSaving(false); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 overflow-y-auto bg-bg">
      <div className="pointer-events-none fixed inset-0"
        style={{ background: `radial-gradient(120% 70% at 50% -10%, color-mix(in srgb, ${sc} 16%, transparent), transparent 60%)` }} />

      <div className="relative mx-auto max-w-md px-5 pb-12 pt-6">
        <div className="flex items-center justify-between">
          <button onClick={onClose} className="flex items-center gap-1.5 text-sm text-faint transition-colors hover:text-lantern">
            <X size={18} weight="light" /> back
          </button>
          <span className="text-[11px] font-medium" style={{ color: sc }}>{STATUS_WORD[status]}</span>
        </div>

        <div className="mt-6 flex items-center gap-3">
          <span className="grid h-12 w-12 place-items-center rounded-full"
            style={{ backgroundColor: `color-mix(in srgb, ${cfg.accent} 16%, transparent)` }}>
            <cfg.icon size={26} weight="light" style={{ color: cfg.accent }} />
          </span>
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-faint">{cfg.label}</p>
            <p className="font-wizard text-[30px] leading-none text-ink">
              {data?.today ?? data?.latest ?? '—'}<span className="ml-1 align-top text-sm text-faint">{cfg.unit}</span>
            </p>
          </div>
        </div>

        {/* the chart */}
        <div className="mt-7 rounded-card border border-line bg-surface p-4">
          {bars.length ? (
            <div className="flex h-32 items-end gap-1.5">
              {bars.map((b: any, i: number) => (
                <motion.div key={b.date + i} className="flex flex-1 flex-col items-center justify-end gap-1"
                  initial={{ height: 0 }} animate={{ height: '100%' }} transition={{ delay: i * 0.03 }}>
                  <motion.span
                    className="w-full rounded-t-md"
                    style={{ backgroundColor: sc, minHeight: 3 }}
                    initial={{ height: 0 }} animate={{ height: `${Math.max(6, (b.value / max) * 100)}%` }}
                    transition={{ duration: 0.5, delay: i * 0.03, ease: 'easeOut' }}
                  />
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="grid h-32 place-items-center text-sm text-faint">No history yet — your first entry starts the line.</p>
          )}
          {bars.length > 0 && (
            <div className="mt-2 flex justify-between text-[10px] text-faint">
              <span>{bars[0].date.slice(5)}</span><span>{bars[bars.length - 1].date.slice(5)}</span>
            </div>
          )}
        </div>

        {/* the wizard's deeper read + the cross-sight */}
        <p className="mt-5 font-wizard text-[17px] leading-relaxed text-ink">{cfg.detail}</p>
        {edge && (
          <div className="mt-3 flex items-start gap-2.5 rounded-xl border border-lantern/25 p-3.5"
            style={{ backgroundColor: 'color-mix(in srgb, var(--lantern) 7%, transparent)' }}>
            <LinkIcon size={16} weight="light" className="mt-0.5 shrink-0 text-lantern" />
            <p className="font-wizard text-[14px] leading-relaxed text-ink">{edge}</p>
          </div>
        )}

        {/* recovery actions */}
        <div className="mt-6">
          <p className="mb-2.5 text-[11px] uppercase tracking-[0.2em] text-faint">a small next step</p>
          <div className="flex flex-wrap gap-2">
            {cfg.recovery.map((a, i) => {
              const Icon = ACTION_ICON[a.kind as keyof typeof ACTION_ICON];
              return (
                <button key={i} onClick={() => onAction(a)}
                  className="flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-2.5 text-sm text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
                  <Icon size={16} weight="light" /> {a.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* the log form (dimensions that take a value here) */}
        {cfg.valueKey && (
          <div className="mt-7 rounded-card border border-line bg-surface p-4">
            <p className="mb-3 text-[11px] uppercase tracking-[0.2em] text-faint">log right now</p>
            <div className="flex items-center gap-2">
              <input type="number" step={cfg.step} value={val} onChange={(e) => setVal(e.target.value)}
                placeholder={`today’s ${cfg.label.toLowerCase()}`}
                className="w-28 rounded-xl border border-line bg-bg px-3 py-2.5 text-[15px] text-ink outline-none transition-colors focus:border-lantern/60" />
              <span className="text-sm text-faint">{cfg.unit}</span>
              <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="a note (optional)"
                className="flex-1 rounded-xl border border-line bg-bg px-3 py-2.5 text-sm text-ink outline-none transition-colors placeholder:text-faint focus:border-lantern/60" />
            </div>
            <button onClick={save} disabled={val === '' || saving}
              className="mt-3 w-full rounded-full bg-lantern py-2.5 text-sm font-medium text-bg transition-all hover:bg-ember hover:shadow-[0_0_20px_rgba(224,162,58,0.4)] disabled:opacity-40">
              {saving ? 'Saving…' : 'Add to the thread'}
            </button>
          </div>
        )}
      </div>
    </motion.div>
  );
}
