import { useCallback, useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CaretDown } from '@phosphor-icons/react';
import { getLifeStats, getDims, postLifeLog } from '../lib/api';
import { DIM_BY_ID, STATUS_COLOR, statusOf } from '../lib/dimensions';
import { LIFE_MODELS } from '../lib/lifeModel';
import { DimensionCard } from '../components/cards/DimensionCard';
import { DimensionDetail } from '../components/cards/DimensionDetail';
import { JournalCard } from '../components/cards/JournalCard';
import { BreathingSession } from '../components/session/BreathingSession';
import { MotifMark } from '../components/brand/MotifMark';
import { Bells } from '../components/bells/Bells';

const PATTERNS = {
  unwind: { inhale: 4, hold_in: 2, exhale: 6, hold_out: 0, cycles: 5 },
  box: { inhale: 4, hold_in: 4, exhale: 4, hold_out: 4, cycles: 6 },
};
const PATTERN_LABEL = { unwind: 'Unwind', box: 'Box breath' } as const;
// Calm grouping: four rooms instead of a thirteen-card wall. The core
// nine keep their order and weight; the five quiet cards share one
// low-voice section at the end, de-emphasized but never hidden.
const SECTIONS: { title: string; sub: string; ids: string[]; quiet?: boolean }[] = [
  { title: 'Body', sub: 'sleep, water, food, motion', ids: ['sleep', 'hydration', 'nutrition', 'fitness'] },
  { title: 'Mind & heart', sub: 'attention, weather, people', ids: ['focus', 'mental', 'social'] },
  { title: 'Momentum', sub: 'threads kept, aims in motion', ids: ['habits', 'goals'] },
  { title: 'Quiet care', sub: 'noticed, never judged', ids: ['spending', 'substance', 'reading', 'medication'], quiet: true },
];

/** Worst status in a section drives its header dot: tending outranks all. */
function sectionStatus(ids: string[], stats: any): 'empty' | 'tending' | 'steady' | 'thriving' {
  let worst: 'empty' | 'tending' | 'steady' | 'thriving' = 'empty';
  let anyData = false;
  for (const id of ids) {
    const cfg = DIM_BY_ID[id];
    if (!cfg) continue;
    const st = statusOf(cfg, stats?.[id]);
    if (st !== 'empty') anyData = true;
    if (st === 'tending') return 'tending';
    if (st === 'thriving') worst = 'thriving';
    else if (st === 'steady' && worst !== 'thriving') worst = 'steady';
  }
  return anyData ? worst : 'empty';
}

/** One honest line for a collapsed section: what's alive, what asks. */
function sectionSummary(ids: string[], stats: any): string {
  let alive = 0, needy = 0;
  for (const id of ids) {
    const cfg = DIM_BY_ID[id];
    if (!cfg) continue;
    const st = statusOf(cfg, stats?.[id]);
    if (st !== 'empty') alive += 1;
    if (st === 'tending') needy += 1;
  }
  if (needy > 0) return `${needy} thread${needy === 1 ? '' : 's'} asking for a look · ${alive} kept`;
  if (alive > 0) return `${alive} thread${alive === 1 ? '' : 's'} quietly kept`;
  return 'resting quietly — open when curious';
}
const SPAN2 = new Set(['sleep', 'goals']);
const LOG_KINDS = new Set(['water', 'sleep', 'nutrition', 'fitness', 'focus', 'stress', 'meditation', 'gratitude', 'habit', 'goal', 'spending', 'social', 'substance', 'reading', 'medication']);

export function Life({ onCheckIn, initialDim, onDimOpened }: { onCheckIn?: () => void; initialDim?: string | null; onDimOpened?: () => void }) {
  const [stats, setStats] = useState<any>(null);
  const [dims, setDims] = useState<any>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [breath, setBreath] = useState<null | 'unwind' | 'box'>(null);
  const [toast, setToast] = useState<{ msg: string; err?: boolean; key: number } | null>(null);
  // Quiet care starts collapsed unless something inside asks for a look.
  // An explicit tap is remembered; otherwise the section follows the data.
  const [quietOpen, setQuietOpen] = useState<boolean | null>(null);
  useEffect(() => {
    try {
      const v = localStorage.getItem('motif-quiet');
      if (v === '1' || v === '0') setQuietOpen(v === '1');
    } catch { /* private mode — stay automatic */ }
  }, []);
  const toggleQuiet = () => {
    setQuietOpen((prev) => {
      const next = !(prev ?? quietAutoOpen);
      try { localStorage.setItem('motif-quiet', next ? '1' : '0'); } catch { /* ignore */ }
      return next;
    });
  };

  const load = useCallback(async () => {
    const [s, d] = await Promise.all([getLifeStats(), getDims()]);
    setStats(s);
    setDims(d);
  }, []);

  useEffect(() => { load().catch(() => {}); }, [load]);

  useEffect(() => {
    if (initialDim) { setOpenId(initialDim); onDimOpened?.(); }
  }, [initialDim, onDimOpened]);

  const quietAutoOpen = useMemo(() => {
    const sec = SECTIONS.find((s) => s.quiet);
    if (!sec || !stats) return false;
    return sectionStatus(sec.ids, stats) === 'tending';
  }, [stats]);
  const quietShown = quietOpen ?? quietAutoOpen;

  const showToast = (msg: string, err = false) => {
    const key = Date.now();
    setToast({ msg, err, key });
    setTimeout(() => setToast((t) => (t && t.key === key ? null : t)), 2400);
  };

  const onAction = async (a: any) => {
    if (!a) return;
    if (a.kind === 'breathe') { setBreath(a.pattern || 'unwind'); return; }
    if (a.kind === 'checkin') { setOpenId(null); onCheckIn?.(); return; }
    if (LOG_KINDS.has(a.kind)) {
      try {
        await postLifeLog(a.kind, a.payload || {});
        await load();
        showToast('Logged ✓');
      } catch {
        showToast('Could not log — try again', true);
      }
    }
  };

  const onLog = async (kind: string, payload: any) => {
    try {
      await postLifeLog(kind, payload);
      await load();
      showToast('Saved ✓');
    } catch {
      showToast('Could not save — try again', true);
    }
  };

  const openCfg = openId ? DIM_BY_ID[openId] : null;
  const openModel = openId ? LIFE_MODELS[openId] : null;
  const openRecords = openId && dims ? dims[openId] : null;

  return (
    <div className="relative h-full overflow-y-auto">
      <Bells />
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-lantern blur-[120px] opacity-10" />
      </div>

      <div className="relative space-y-4 pb-10 pt-2">
        <header>
          <p className="text-[11px] uppercase tracking-[0.25em] text-faint">the heart of it</p>
          <h1 className="mt-1 font-wizard text-[32px] leading-none">Your life, held together</h1>
          <p className="mt-2.5 max-w-sm font-wizard text-[15px] leading-snug text-muted">
            Thirteen threads of one life — logged gently, read honestly.
          </p>
        </header>

        {!stats ? (
          <div className="grid h-40 place-items-center"><MotifMark size={56} /></div>
        ) : (
          <div className="space-y-7">
            {SECTIONS.map((sec, si) => {
              const dot = sectionStatus(sec.ids, stats);
              const dotColor = STATUS_COLOR[dot];
              const collapsed = !!sec.quiet && !quietShown;
              return (
                <section key={sec.title}>
                  <button
                    onClick={sec.quiet ? toggleQuiet : undefined}
                    className={'flex w-full items-center gap-2.5 text-left ' + (sec.quiet ? 'cursor-pointer' : 'cursor-default')}
                    aria-expanded={sec.quiet ? !collapsed : undefined}
                  >
                    <motion.span
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ background: dotColor }}
                      animate={dot === 'tending' ? { opacity: [1, 0.35, 1] } : { opacity: 1 }}
                      transition={dot === 'tending' ? { duration: 2.4, repeat: Infinity, ease: 'easeInOut' } : {}}
                    />
                    <span>
                      <span className="block text-[11px] uppercase tracking-[0.25em] text-faint">{sec.title}</span>
                      <span className="mb-1 mt-0.5 block font-wizard text-[13px] text-muted">
                        {collapsed ? sectionSummary(sec.ids, stats) : sec.sub}
                      </span>
                    </span>
                    {sec.quiet ? (
                      <motion.span
                        className="ml-auto grid h-7 w-7 shrink-0 place-items-center rounded-full border border-line text-muted"
                        animate={{ rotate: collapsed ? 0 : 180 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 26 }}
                      >
                        <CaretDown size={14} />
                      </motion.span>
                    ) : null}
                  </button>
                  <AnimatePresence initial={false}>
                    {!collapsed ? (
                      <motion.div
                        key="grid"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.32, ease: [0.32, 0.72, 0, 1] }}
                        className="overflow-hidden"
                      >
                        <div className="grid grid-cols-2 gap-3 pt-2">
                          {sec.ids.map((id, ci) => {
                            const cfg = DIM_BY_ID[id];
                            const model = LIFE_MODELS[id];
                            const d = stats[id];
                            if (!cfg || !model) return null;
                            return (
                              <motion.div
                                key={id}
                                className={(SPAN2.has(id) ? 'col-span-2 ' : '') + 'min-w-0'}
                                initial={{ opacity: 0, y: 14 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.45, delay: Math.min(0.05 * (si * 3 + ci), 0.4), ease: 'easeOut' }}
                              >
                                <DimensionCard cfg={cfg} model={model} data={d} hero={SPAN2.has(id)}
                                  onOpen={() => setOpenId(id)} onAction={onAction} />
                              </motion.div>
                            );
                          })}
                        </div>
                      </motion.div>
                    ) : null}
                  </AnimatePresence>
                </section>
              );
            })}
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2 min-w-0"><JournalCard /></div>
            </div>
          </div>
        )}
      </div>

      <AnimatePresence>
        {openCfg && openModel && (
          <DimensionDetail cfg={openCfg} model={openModel} data={stats?.[openModel.id]}
            records={openRecords} onClose={() => setOpenId(null)} onLog={onLog}
            onBreathe={() => setBreath('unwind')}
            onCheckin={() => { setOpenId(null); onCheckIn?.(); }} />
        )}
      </AnimatePresence>

      {breath && (
        <BreathingSession config={{ name: PATTERN_LABEL[breath], breathing_pattern: PATTERNS[breath] }}
          state="tending" severityBefore={0}
          onComplete={() => setBreath(null)} onClose={() => setBreath(null)}
          completeHeading="You gave yourself a moment."
          completeBody="However small, that tending matters. Carry its calm back with you."
          completeLabel="Carry it with you" />
      )}

      <AnimatePresence>
        {toast && (
          <motion.div key={toast.key} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="fixed bottom-6 left-1/2 z-[70] -translate-x-1/2 rounded-full px-5 py-2.5 text-sm font-medium shadow-xl"
            style={{ background: toast.err ? 'var(--mood-angry)' : 'var(--sage)', color: 'var(--bg)' }}>
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
