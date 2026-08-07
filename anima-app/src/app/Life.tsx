import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { getLifeStats, postLifeLog } from '../lib/api';
import { DIM_BY_ID } from '../lib/dimensions';
import { LIFE_MODELS } from '../lib/lifeModel';
import { DimensionCard } from '../components/cards/DimensionCard';
import { DimensionDetail } from '../components/cards/DimensionDetail';
import { JournalCard } from '../components/cards/JournalCard';
import { BreathingSession } from '../components/session/BreathingSession';
import { MotifMark } from '../components/brand/MotifMark';

const PATTERNS = {
  unwind: { inhale: 4, hold_in: 2, exhale: 6, hold_out: 0, cycles: 5 },
  box: { inhale: 4, hold_in: 4, exhale: 4, hold_out: 4, cycles: 6 },
};
const PATTERN_LABEL = { unwind: 'Unwind', box: 'Box breath' } as const;

const ORDER = ['sleep', 'hydration', 'nutrition', 'fitness', 'focus', 'mental', 'habits', 'goals'];
const SPAN2 = new Set(['sleep', 'goals']);
const LOG_KINDS = new Set(['water', 'sleep', 'nutrition', 'fitness', 'focus', 'stress', 'meditation', 'gratitude', 'habit', 'goal']);

export function Life({ onCheckIn }: { onCheckIn?: () => void }) {
  const [stats, setStats] = useState<any>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [breath, setBreath] = useState<null | 'unwind' | 'box'>(null);

  const load = () => getLifeStats().then(setStats).catch(() => {});
  useEffect(() => { load(); }, []);

  const aggregate = stats
    ? 'Eight threads of one life — logged gently, read honestly.'
    : 'Gathering your threads…';

  const onAction = async (a: { kind: string; payload?: any; pattern?: 'unwind' | 'box' }) => {
    if (!a) return;
    if (a.kind === 'breathe') { setBreath(a.pattern || 'unwind'); return; }
    if (a.kind === 'checkin') { setOpenId(null); onCheckIn?.(); return; }
    if (LOG_KINDS.has(a.kind)) {
      await postLifeLog(a.kind, a.payload || {});
      await load();
    }
  };

  const onLogged = async (kind: string, values: Record<string, any>) => {
    await postLifeLog(kind, values);
    await load();
  };

  const openCfg = openId ? DIM_BY_ID[openId] : null;
  const openModel = openId ? LIFE_MODELS[openId] : null;

  return (
    <div className="relative h-full overflow-y-auto">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-lantern blur-[120px] opacity-10" />
      </div>

      <div className="relative space-y-4 pb-10 pt-2">
        <header>
          <p className="text-[11px] uppercase tracking-[0.25em] text-faint">the heart of it</p>
          <h1 className="mt-1 font-wizard text-[32px] leading-none">Your life, held together</h1>
          <motion.p key={aggregate} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
            className="mt-2.5 max-w-sm font-wizard text-[15px] leading-snug text-muted">{aggregate}</motion.p>
        </header>

        {!stats ? (
          <div className="grid h-40 place-items-center"><MotifMark size={56} /></div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {ORDER.map((id) => {
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
            <div className="col-span-2 min-w-0"><JournalCard /></div>
          </div>
        )}
      </div>

      <AnimatePresence>
        {openCfg && openModel && (
          <DimensionDetail
            cfg={openCfg} model={openModel} data={stats?.[openModel.id]}
            onClose={() => setOpenId(null)}
            onQuick={onAction}
            onBreathe={() => setBreath('unwind')}
            onCheckin={() => { setOpenId(null); onCheckIn?.(); }}
            onLogged={onLogged}
          />
        )}
      </AnimatePresence>

      {breath && (
        <BreathingSession
          config={{ name: PATTERN_LABEL[breath], breathing_pattern: PATTERNS[breath] }}
          state="tending" severityBefore={0}
          onComplete={() => setBreath(null)} onClose={() => setBreath(null)}
          completeHeading="You gave yourself a moment."
          completeBody="However small, that tending matters. Carry its calm back with you."
          completeLabel="Carry it with you"
        />
      )}
    </div>
  );
}
