import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendUp, Trophy } from '@phosphor-icons/react';
import { getInsights, streamReflection } from '../lib/api';
import { MotifMark } from '../components/brand/MotifMark';
import { RhythmCard } from '../components/cards/RhythmCard';

const CACHE_KEY = 'motif-reflection';

function todayStr(): string {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${m}-${day}`;
}

interface CachedReflection { signature: string; day: string; text: string; }

function loadCache(): CachedReflection | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const p = JSON.parse(raw);
    if (p && typeof p.text === 'string' && p.signature && p.day) return p as CachedReflection;
  } catch { /* ignore */ }
  return null;
}

function saveCache(c: CachedReflection) {
  try { localStorage.setItem(CACHE_KEY, JSON.stringify(c)); } catch { /* ignore */ }
}

function Cursor() {
  return (
    <motion.span
      className="ml-1 inline-block h-4 w-1.5 translate-y-0.5 rounded-full bg-lantern"
      animate={{ opacity: [1, 0.2, 1] }}
      transition={{ duration: 0.9, repeat: Infinity }}
    />
  );
}

function ThinkingDots() {
  return (
    <span className="inline-flex items-center gap-1.5 pt-1">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-lantern"
          animate={{ opacity: [0.25, 1, 0.25] }}
          transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </span>
  );
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

export function Insights() {
  const [data, setData] = useState<any>(null);
  const [reflection, setReflection] = useState('');
  const [reflecting, setReflecting] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  /**
   * Generate a fresh reflection and cache it on clean completion.
   * Each call owns its abort signal + accumulator, so an aborted stream
   * (e.g. navigating away) never saves a half-finished sentence.
   */
  const reflect = (signature: string) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    const signal = controller.signal;
    let pending = '';
    const day = todayStr();
    setReflecting(true);
    setReflection('');
    streamReflection(
      (t) => { if (signal.aborted) return; pending += t; setReflection(pending); },
      () => {
        if (signal.aborted) return;          // torn down → don't finalise or cache
        setReflecting(false);
        if (pending.trim()) saveCache({ signature, day, text: pending });
      },
      signal,
    ).catch(() => { if (!signal.aborted) setReflecting(false); });
  };

  useEffect(() => {
    let cancelled = false;
    getInsights()
      .then((d) => {
        if (cancelled) return;
        setData(d);
        const sig = d?.signature ?? '';
        const day = todayStr();
        const cached = loadCache();
        // Cache hit → instant, no LLM. Miss (new data or new day) → generate once.
        if (cached && cached.signature === sig && cached.day === day && cached.text) {
          setReflection(cached.text);
        } else {
          reflect(sig);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
      controllerRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const wins = data?.wins || [];
  const effective = data?.effective || [];

  return (
    <div className="relative h-full overflow-y-auto">
      <div className="pointer-events-none absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-lantern blur-[120px] opacity-10" />

      <div className="relative space-y-7 pb-8 pt-2">
        <div>
          <h1 className="font-wizard text-[28px] leading-tight">What I've noticed</h1>
          <p className="mt-1 text-sm text-muted">Reflections from watching over you.</p>
        </div>

        <div className="rounded-card border border-lantern/25 bg-surface p-5 shadow-[0_0_30px_rgba(245,184,65,0.06)]">
          <div className="flex items-center gap-2.5">
            <MotifMark size={24} />
            <span className="font-wizard text-lg">The wizard reflects</span>
          </div>
          <div className="mt-3 text-[16px] leading-relaxed">
            {reflection ? (
              <span className="font-wizard text-ink">
                {reflection}
                {reflecting && <Cursor />}
              </span>
            ) : reflecting ? (
              <ThinkingDots />
            ) : (
              <span className="text-faint">Tap below to hear what I've noticed.</span>
            )}
          </div>
          <button
            onClick={() => reflect(data?.signature ?? '')}
            disabled={reflecting}
            className="mt-4 rounded-full border border-line px-5 py-2 text-sm text-muted transition-colors hover:border-lantern/50 hover:text-lantern disabled:opacity-50"
          >
            {reflecting ? 'Reflecting…' : 'Reflect again'}
          </button>
        </div>

        <RhythmCard />

        {effective.length > 0 && (
          <section>
            <h2 className="mb-3 flex items-center gap-2 font-wizard text-lg">
              <TrendUp size={20} weight="light" className="text-sage" /> What's helping
            </h2>
            <div className="space-y-2.5">
              {effective.map((iv: any) => (
                <div key={iv.name} className="rounded-card border border-line bg-surface p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium">{iv.name}</p>
                    {iv.avg_improvement != null && iv.avg_improvement > 0 && (
                      <span className="shrink-0 text-sm text-sage">
                        {'↓'} {iv.avg_improvement} pts
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-faint">
                    Used {iv.times_used} time{iv.times_used !== 1 ? 's' : ''}
                    {iv.state ? ` for ${iv.state}` : ''}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section>
          <h2 className="mb-3 flex items-center gap-2 font-wizard text-lg">
            <Trophy size={20} weight="light" className="text-lantern" /> Wins to savor
          </h2>
          {wins.length > 0 ? (
            <div className="space-y-2.5">
              {wins.map((w: any, i: number) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="rounded-card border border-lantern/20 bg-surface p-4"
                >
                  <p className="font-wizard text-[15px] leading-relaxed">{w.description}</p>
                  {w.timestamp && (
                    <p className="mt-1.5 text-xs text-faint">{formatDate(w.timestamp)}</p>
                  )}
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="rounded-card border border-line bg-surface p-4 text-sm leading-relaxed text-faint">
              No wins logged yet. When something goes well, tell me — I'll keep it safe for the harder days.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
