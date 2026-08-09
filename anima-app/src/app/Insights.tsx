import { useEffect, useState } from 'react';
import { getMirror } from '../lib/api';
import { MotifMark } from '../components/brand/MotifMark';

const ROWS = [
  { key: 'mood', label: 'mood', color: 'var(--sage)' },
  { key: 'sleep', label: 'sleep', color: 'var(--mood-calm)' },
  { key: 'move', label: 'move', color: 'var(--ember)' },
  { key: 'focus', label: 'focus', color: 'var(--lantern)' },
  { key: 'calm', label: 'calm', color: 'var(--sage)' },
];

export function Insights() {
  const [m, setM] = useState<any>(null);
  useEffect(() => { getMirror().then(setM).catch(() => {}); }, []);
  if (!m) return <div className="grid h-60 place-items-center"><MotifMark size={56} /></div>;
  return (
    <div className="relative h-full overflow-y-auto">
      <div className="relative space-y-4 pb-10 pt-2">
        <header>
          <p className="text-[11px] uppercase tracking-[0.25em] text-faint">the mirror</p>
          <h1 className="mt-1 font-wizard text-[28px] leading-tight">What your days are saying</h1>
          {m.reflection && <p className="mt-3 font-wizard text-[16px] leading-snug text-muted">{m.reflection}</p>}
        </header>
        <div className="rounded-card border border-line bg-surface p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">the week's weave</p>
          <div className="mt-3 space-y-2">
            {ROWS.map((row) => (
              <div key={row.key} className="flex items-center gap-2">
                <span className="w-12 text-[10px] text-faint">{row.label}</span>
                <div className="flex flex-1 gap-1.5">
                  {(m.tapestry || []).map((d: any) => (
                    <div key={d.date} className="h-6 flex-1 rounded-md" title={d.date}
                      style={{ background: row.color, opacity: d[row.key] == null ? 0.08 : 0.15 + d[row.key] * 0.85 }} />
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[10px] text-faint">brighter = more of it that day. watch the rows rise and fall together.</p>
        </div>
        <div className="space-y-2">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">the threads between</p>
          {(m.threads || []).length === 0 && <p className="text-sm text-faint">not enough days yet to see the threads. keep living; the mirror is patient.</p>}
          {(m.threads || []).map((t: any) => (
            <div key={t.a + t.b} className="rounded-card border border-line bg-surface p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-ink">{t.a} ↔ {t.b}</p>
                <span className="text-[10px] text-faint">{Math.round(t.strength * 100)}% woven</span>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-line/40">
                <div className="h-full rounded-full bg-lantern" style={{ width: t.strength * 100 + '%' }} />
              </div>
              <p className="mt-2 font-wizard text-[14px] leading-snug text-muted">{t.text}</p>
            </div>
          ))}
        </div>
        <div className="rounded-card border border-line bg-surface p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">this week vs last</p>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {(m.trends || []).map((t: any) => (
              <div key={t.dim} className="flex items-center justify-between rounded-lg border border-line bg-bg px-3 py-2">
                <span className="text-xs text-muted">{t.dim}</span>
                <span className="text-xs" style={{ color: t.dir === 'up' ? 'var(--sage)' : t.dir === 'down' ? 'var(--ember)' : 'var(--faint)' }}>
                  {t.dir === 'up' ? 'rising' : t.dir === 'down' ? 'easing' : 'steady'}
                </span>
              </div>
            ))}
          </div>
        </div>
        {m.question && (
          <div className="rounded-card border border-lantern/30 bg-surface p-5">
            <p className="text-[11px] uppercase tracking-[0.2em] text-faint">a question to sit with</p>
            <p className="mt-2 font-wizard text-[17px] leading-snug text-ink">{m.question}</p>
          </div>
        )}
      </div>
    </div>
  );
}
