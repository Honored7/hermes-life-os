import { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Wind, ChatTeardrop, Plus } from '@phosphor-icons/react';
import type { DimConfig } from '../../lib/dimensions';
import type { DimModel } from '../../lib/lifeModel';

const fmtKey = (k: string) => k.replace(/_/g, ' ');
const fmtVal = (v: any) =>
  Array.isArray(v) ? (v.length ? v.join(', ') : '—') : v == null ? '—' : String(v);

export function DimensionDetail({
  cfg, model, data, onClose, onQuick, onBreathe, onCheckin, onLogged,
}: {
  cfg: DimConfig; model: DimModel; data: any;
  onClose: () => void;
  onQuick: (q: { kind: string; payload?: any }) => void;
  onBreathe: () => void;
  onCheckin: () => void;
  onLogged: (kind: string, values: Record<string, any>) => Promise<void>;
}) {
  const [form, setForm] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const week = data?.week || {};
  const series = data?.series || [];
  const unit = data?.unit || model.unit;
  const today = data?.today ?? null;
  const max = Math.max(1, ...series.map((s: any) => s.value));
  const weekRows = Object.entries(week);

  const submit = async () => {
    setSaving(true);
    try { await onLogged(model.logKind, form); setForm({}); }
    finally { setSaving(false); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 overflow-y-auto bg-bg">
      <div className="pointer-events-none fixed inset-0"
        style={{ background: `radial-gradient(120% 70% at 50% -10%, color-mix(in srgb, ${cfg.accent} 14%, transparent), transparent 60%)` }} />
      <div className="relative mx-auto max-w-md px-5 pb-12 pt-6">
        <div className="flex items-center justify-between">
          <button onClick={onClose} className="flex items-center gap-1.5 text-sm text-faint transition-colors hover:text-lantern">
            <X size={18} weight="light" /> back
          </button>
        </div>

        <div className="mt-5 flex items-center gap-3">
          <span className="grid h-12 w-12 place-items-center rounded-full"
            style={{ backgroundColor: `color-mix(in srgb, ${cfg.accent} 16%, transparent)` }}>
            <cfg.icon size={26} weight="light" style={{ color: cfg.accent }} />
          </span>
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-faint">{cfg.label}</p>
            <p className="font-wizard text-[30px] leading-none text-ink">
              {today != null ? Number(today) : '—'}<span className="ml-1 align-top text-sm text-faint">{unit}</span>
            </p>
          </div>
        </div>

        <p className="mt-3 font-wizard text-[15px] leading-snug text-muted">{model.opener}</p>

        {weekRows.length > 0 && (
          <div className="mt-5 rounded-card border border-line bg-surface p-4">
            <p className="mb-3 text-[11px] uppercase tracking-[0.2em] text-faint">this week</p>
            <div className="grid grid-cols-2 gap-3">
              {weekRows.map(([k, v]) => (
                <div key={k} className="rounded-xl bg-bg px-3 py-2.5">
                  <p className="text-[10px] uppercase tracking-wider text-faint">{fmtKey(k)}</p>
                  <p className="mt-0.5 truncate font-wizard text-[16px] text-ink">{fmtVal(v)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {series.length > 0 && (
          <div className="mt-4 rounded-card border border-line bg-surface p-4">
            <p className="mb-3 text-[11px] uppercase tracking-[0.2em] text-faint">last 7 days</p>
            <div className="flex h-24 items-end gap-1.5">
              {series.map((s: any, i: number) => (
                <motion.span key={s.date + i} className="flex-1 rounded-t-md"
                  style={{ backgroundColor: cfg.accent, minHeight: 3 }}
                  initial={{ height: 0 }} animate={{ height: `${Math.max(6, (s.value / max) * 100)}%` }}
                  transition={{ duration: 0.5, delay: i * 0.04, ease: 'easeOut' }} />
              ))}
            </div>
            <div className="mt-2 flex justify-between text-[10px] text-faint">
              <span>{series[0]?.date.slice(5)}</span><span>{series[series.length - 1]?.date.slice(5)}</span>
            </div>
          </div>
        )}

        <div className="mt-4 rounded-card border border-line bg-surface p-4">
          <p className="mb-3 text-[11px] uppercase tracking-[0.2em] text-faint">log right now</p>
          <div className="space-y-2.5">
            {model.fields.map((f) => (
              <label key={f.key} className="block">
                <span className="mb-1 block text-[11px] text-faint">{f.label}</span>
                <input
                  type={f.type === 'number' ? 'number' : 'text'}
                  value={form[f.key] ?? ''}
                  onChange={(e) => setForm((p) => ({ ...p, [f.key]: e.target.value }))}
                  placeholder={f.placeholder}
                  className="w-full rounded-xl border border-line bg-bg px-3 py-2.5 text-[15px] text-ink outline-none transition-colors placeholder:text-faint focus:border-lantern/60"
                />
              </label>
            ))}
          </div>
          <button onClick={submit} disabled={saving}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-lantern py-2.5 text-sm font-medium text-bg transition-all hover:bg-ember hover:shadow-[0_0_20px_rgba(224,162,58,0.4)] disabled:opacity-40">
            <Plus size={16} weight="light" /> {saving ? 'Saving…' : 'Add to the thread'}
          </button>
        </div>

        <div className="mt-4">
          <p className="mb-2.5 text-[11px] uppercase tracking-[0.2em] text-faint">a small next step</p>
          <div className="flex flex-wrap gap-2">
            {model.quickLogs.map((q, i) => (
              <button key={i} onClick={() => onQuick(q)}
                className="rounded-full border border-line bg-surface px-4 py-2.5 text-sm text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
                {q.label}
              </button>
            ))}
            <button onClick={onBreathe}
              className="flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-2.5 text-sm text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
              <Wind size={16} weight="light" /> A calming breath
            </button>
            <button onClick={onCheckin}
              className="flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-2.5 text-sm text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
              <ChatTeardrop size={16} weight="light" /> Check in with the wizard
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
