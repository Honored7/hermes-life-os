import { useCallback, useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { getLifeStats, getDims, postLifeLog } from '../lib/api';
import { DIM_BY_ID } from '../lib/dimensions';
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
const SECTIONS: { title: string; sub: string; ids: string[] }[] = [
  { title: 'Body', sub: 'sleep, water, food, motion', ids: ['sleep', 'hydration', 'nutrition', 'fitness'] },
  { title: 'Mind & heart', sub: 'attention, weather, people', ids: ['focus', 'mental', 'social'] },
  { title: 'Momentum', sub: 'threads kept, aims in motion', ids: ['habits', 'goals'] },
  { title: 'Quiet care', sub: 'noticed, never judged', ids: ['spending', 'substance', 'reading', 'medication'] },
];
const SPAN2 = new Set(['sleep', 'goals']);
const LOG_KINDS = new Set(['water', 'sleep', 'nutrition', 'fitness', 'focus', 'stress', 'meditation', 'gratitude', 'habit', 'goal', 'spending', 'social', 'substance', 'reading', 'medication']);

export function Life({ onCheckIn, initialDim, onDimOpened }: { onCheckIn?: () => void; initialDim?: string | null; onDimOpened?: () => void }) {
  const [stats, setStats] = useState<any>(null);
  const [dims, setDims] = useState<any>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [breath, setBreath] = useState<null | 'unwind' | 'box'>(null);
  const [toast, setToast] = useState<{ msg: string; err?: boolean; key: number } | null>(null);

  const load = useCallback(async () => {
    const [s, d] = await Promise.all([getLifeStats(), getDims()]);
    setStats(s);
    setDims(d);
  }, []);

  useEffect(() => { load().catch(() => {}); }, [load]);

  useEffect(() => {
    if (initialDim) { setOpenId(initialDim); onDimOpened?.(); }
  }, [initialDim, onDimOpened]);

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
            {SECTIONS.map((sec) => (
              <section key={sec.title}>
                <p className="text-[11px] uppercase tracking-[0.25em] text-faint">{sec.title}</p>
                <p className="mb-3 mt-0.5 font-wizard text-[13px] text-muted">{sec.sub}</p>
                <div className="grid grid-cols-2 gap-3">
                  {sec.ids.map((id) => {
                    const cfg = DIM_BY_ID[id];
                    const model = LIFE_MODELS[id];
                    const d = stats[id];
                    if (!cfg || !model) return null;
                    return (
                      <div key={id} className={(SPAN2.has(id) ? 'col-span-2 ' : '') + 'min-w-0'}>
                        <DimensionCard cfg={cfg} model={model} data={d} hero={SPAN2.has(id)}
                          onOpen={() => setOpenId(id)} onAction={onAction} />
                      </div>
                    );
                  })}
                </div>
              </section>
            ))}
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
