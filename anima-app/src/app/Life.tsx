import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { getDimensionStats } from '../lib/api';
import { DIMS, DIM_BY_ID } from '../lib/dimensions';
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

// layout rhythm: the two richest are hero strips; goals closes full-width
const HERO = new Set(['sleep', 'mood']);
const FULL = new Set(['goals']);

export function Life({ onCheckIn }: { onCheckIn?: () => void }) {
  const [stats, setStats] = useState<any>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [breath, setBreath] = useState<null | 'unwind' | 'box'>(null);

  const load = () => getDimensionStats().then(setStats).catch(() => {});
  useEffect(() => { load(); }, []);

  const statuses = DIMS.map((d) => {
    const s = stats?.dims?.[d.id];
    const series = s?.series || [];
    const last = series.length ? series[series.length - 1].date : null;
    const days = last ? Math.floor((Date.now() - new Date(last + 'T12:00:00').getTime()) / 86400000) : 99;
    const cur = s?.today ?? s?.latest ?? null;
    if (!series.length && cur == null) return 'empty';
    if (days > 3) return 'tending';
    if (d.target != null && cur != null && cur >= d.target) return 'thriving';
    if (d.target != null && cur != null && cur < d.target * 0.6) return 'tending';
    return 'steady';
  });
  const thriving = statuses.filter((s) => s === 'thriving').length;
  const tending = statuses.filter((s) => s === 'tending').length;
  const empty = statuses.filter((s) => s === 'empty').length;
  const aggregate =
    empty === DIMS.length ? 'A fresh canvas — tend one thread, and the rest will follow.' :
    tending >= 3 ? `A few threads could use a little tending. Pick the one that calls to you — just one.` :
    thriving >= 3 ? `${thriving} threads are thriving. You’re tending your life like it matters, because it does.` :
    `A mixed, honest week — some threads strong, some asking for you. That’s a real life, held together.`;

  const onAction = (a: { kind: string; pattern?: 'unwind' | 'box' }) => {
    if (a.kind === 'breathe') setBreath(a.pattern || 'unwind');
    else if (a.kind === 'checkin') { setOpenId(null); onCheckIn?.(); }
    else if (a.kind === 'journal') { /* journal opens itself via its card; for recovery, nudge detail close */ setOpenId(null); }
    else if (a.kind === 'log') { /* focus the form: open the relevant detail if on a card */ }
  };

  const openCfg = openId ? DIM_BY_ID[openId] : null;

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
            className="mt-2.5 max-w-sm font-wizard text-[15px] leading-snug text-muted">
            {aggregate}
          </motion.p>
        </header>

        {!stats ? (
          <div className="grid h-40 place-items-center"><MotifMark size={56} /></div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {DIMS.map((d) => (
              <div key={d.id} className={(HERO.has(d.id) || FULL.has(d.id)) ? 'col-span-2' : 'col-span-1'}>
                <DimensionCard
                  cfg={d}
                  data={stats.dims?.[d.id]}
                  edge={stats.edges?.[d.id] || null}
                  hero={HERO.has(d.id)}
                  onOpen={() => setOpenId(d.id)}
                  onAction={onAction}
                />
              </div>
            ))}
            <div className="col-span-2"><JournalCard /></div>
          </div>
        )}
      </div>

      <AnimatePresence>
        {openCfg && (
          <DimensionDetail
            cfg={openCfg}
            data={stats?.dims?.[openCfg.id]}
            edge={stats?.edges?.[openCfg.id] || null}
            onClose={() => setOpenId(null)}
            onAction={onAction}
            onChanged={load}
          />
        )}
      </AnimatePresence>

      {breath && (
        <BreathingSession
          config={{ name: PATTERN_LABEL[breath], breathing_pattern: PATTERNS[breath] }}
          state="tending"
          severityBefore={0}
          onComplete={() => setBreath(null)}
          onClose={() => setBreath(null)}
          completeHeading="You gave yourself a moment."
          completeBody="However small, that tending matters. Carry its calm back with you."
          completeLabel="Carry it with you"
        />
      )}
    </div>
  );
}
