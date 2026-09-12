import { useEffect, useState } from 'react';
import { getClimate, postLifeLog, fetchWhy } from '../lib/api';
import { openDimension } from '../lib/navBus';
import { MotifMark } from '../components/brand/MotifMark';

export function Insights() {
  const [lens, setLens] = useState<'start' | '30'>('start');
  const [c, setC] = useState<any>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [why, setWhy] = useState<Record<string, { loading?: boolean; text?: string; down?: boolean }>>({});
  useEffect(() => { getClimate(lens).then(setC).catch(() => {}); }, [lens]);
  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(null), 4000); return () => clearTimeout(t); }, [toast]);
  if (!c) return <div className="grid h-60 place-items-center"><MotifMark size={56} /></div>;

  const askWhy = async (card: any) => {
    if (why[card.id]?.loading) return;
    setWhy((p) => ({ ...p, [card.id]: { loading: true } }));
    try {
      const r = await fetchWhy(card, lens, c.signals);
      setWhy((p) => ({ ...p, [card.id]: r?.text ? { text: r.text } : { down: true } }));
    } catch {
      setWhy((p) => ({ ...p, [card.id]: { down: true } }));
    }
  };

  return (
    <div className="relative h-full overflow-y-auto">
      <div className="relative space-y-4 pb-10 pt-2">
        <header>
          <p className="text-[11px] uppercase tracking-[0.25em] text-faint">the climate of you</p>
          <h1 className="mt-1 font-wizard text-[24px] leading-tight text-ink">{c.headline}</h1>
          <div className="mt-3 flex gap-2">
            {(['start', '30'] as const).map((l) => (
              <button key={l} onClick={() => setLens(l)}
                className="rounded-full border px-3.5 py-1.5 text-xs transition-all"
                style={{
                  borderColor: lens === l ? 'var(--lantern)' : 'var(--line)',
                  color: lens === l ? 'var(--lantern)' : 'var(--faint)',
                }}>
                {l === 'start' ? 'since you began' : 'last 30 days'}
              </button>
            ))}
          </div>
        </header>

        {(c.cards || []).map((card: any) => (
          <div key={card.id} className="rounded-card border border-line bg-surface p-5"
            style={{ borderColor: card.tone === 'attention' ? 'color-mix(in srgb, var(--ember) 35%, var(--line))' : 'color-mix(in srgb, var(--sage) 35%, var(--line))' }}>
            <div className="flex items-center justify-between">
              <p className="text-[11px] uppercase tracking-[0.2em] text-faint">{card.title}</p>
              <span className="text-[10px]" style={{ color: card.tone === 'attention' ? 'var(--ember)' : 'var(--sage)' }}>
                {card.tone === 'attention' ? 'asking for you' : 'a strength'}
              </span>
            </div>
            <p className="mt-2 font-wizard text-[17px] leading-snug text-ink">{card.finding}</p>
            <p className="mt-1 text-[11px] text-faint">{card.proof}</p>
            <p className="mt-2 text-[13px] leading-snug text-muted">{card.meaning}</p>
            {why[card.id]?.text ? (
              <p className="mt-2 border-l-2 border-lantern/40 pl-3 font-wizard text-[14px] italic leading-snug text-ink">
                {why[card.id].text}
              </p>
            ) : null}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {card.action && (
                <button onClick={async () => { await postLifeLog(card.action.kind, card.action.payload); setToast('added — the companion will remember.'); }}
                  className="rounded-full bg-lantern px-4 py-2 text-xs font-medium text-bg transition-all hover:bg-ember">
                  {card.action.label}
                </button>
              )}
              <button onClick={() => askWhy(card)} disabled={!!why[card.id]?.loading}
                className="rounded-full border border-line px-4 py-2 text-xs text-muted transition-all hover:border-lantern/50 hover:text-lantern disabled:opacity-60">
                {why[card.id]?.loading ? 'listening…' : why[card.id]?.down ? 'quiet right now — retry' : 'why is this so?'}
              </button>
            </div>
          </div>
        ))}
        {(c.steady || []).length > 0 && (
          <p className="text-xs text-faint">steady for now: {c.steady.join(' · ')}</p>
        )}
        {(c.empty || []).length > 0 && (
          <div className="rounded-card border border-dashed border-line bg-surface p-4">
            <p className="text-[11px] uppercase tracking-[0.2em] text-faint">not seen yet</p>
            <p className="mt-2 text-[13px] leading-snug text-muted">
              I haven't seen {c.empty.join(', ')} yet. Each one you tend teaches me — and you — a little more.
            </p>
          </div>
        )}
        <div className="rounded-card border border-line bg-surface p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">look deeper</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {(c.links || []).map((l: string) => (
              <button key={l} onClick={() => openDimension(l)} className="rounded-full border border-line px-3 py-1 text-[11px] text-faint transition-all hover:border-lantern/50 hover:text-lantern">{l} →</button>
            ))}
          </div>
          <p className="mt-2 text-[10px] text-faint">every dimension keeps its full picture in Life — this page only leads with what matters most.</p>
        </div>

        {toast && (
          <div className="fixed bottom-6 left-1/2 z-[80] -translate-x-1/2 rounded-full px-5 py-2.5 text-sm font-medium shadow-xl"
            style={{ background: 'var(--sage)', color: 'var(--bg)' }}>
            {toast}
          </div>
        )}
      </div>
    </div>
  );
}
