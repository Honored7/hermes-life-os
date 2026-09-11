import { useEffect, useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { MoonStars, Sparkle } from '@phosphor-icons/react';
import { MotifMark } from '../brand/MotifMark';
import { getRhythm } from '../../lib/api';

interface SeriesNight { date: string; hours: number; }
interface RhythmData {
  count: number;
  avg_hours: number | null;
  last_hours: number | null;
  series: SeriesNight[];
  poor_streak: number;
  pattern: string | null;
}

const TRACK = 112;            // px height of the bar region
const barH = (h: number) => 8 + (Math.min(Math.max(h, 0), 10) / 10) * (TRACK - 8);
const GUIDE = barH(6);        // the "rest" threshold, on the same scale as the bars

/** A night's tone — warm when it served you, dim when it didn't. */
function toneOf(h: number) {
  if (h >= 7) return { bar: 'var(--lantern)', dot: 'var(--lantern)', glow: true, word: 'restorative' };
  if (h >= 6) return { bar: 'var(--sage)', dot: 'var(--sage)', glow: false, word: 'steady' };
  return { bar: 'var(--faint)', dot: 'var(--ember)', glow: false, word: 'short' };
}

const wd = (date: string) =>
  new Date(date + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'short' });
const dayLong = (date: string) =>
  new Date(date + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });

/** A small odometer for the average — jumps straight to the value under reduced motion. */
function useCountUp(target: number | null, ms = 700) {
  const reduce = useReducedMotion();
  const [v, setV] = useState(target ?? 0);
  useEffect(() => {
    if (target == null) { setV(0); return; }
    if (reduce) { setV(target); return; }
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms);
      const e = 1 - Math.pow(1 - t, 3);
      setV(target * e);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, reduce, ms]);
  return v;
}

export function RhythmCard() {
  const [data, setData] = useState<RhythmData | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const avg = useCountUp(data?.avg_hours ?? null);

  useEffect(() => { getRhythm().then(setData).catch(() => {}); }, []);

  const pill =
    data && data.poor_streak >= 2
      ? { text: `${data.poor_streak} short nights running`, color: 'var(--ember)' }
      : data && data.avg_hours != null && data.avg_hours >= 7
        ? { text: 'resting well lately', color: 'var(--sage)' }
        : null;

  return (
    <div
      className="relative overflow-hidden rounded-card border border-line bg-surface p-5 transition-colors hover:border-lantern/30"
      style={{ backgroundImage: 'radial-gradient(120% 80% at 100% 0%, color-mix(in srgb, var(--lantern) 8%, transparent), transparent 60%)' }}
    >
      <div className="pointer-events-none absolute bottom-2 right-2 opacity-[0.05]"><MotifMark size={92} /></div>

      {/* header */}
      <div className="relative flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-full"
            style={{ backgroundColor: 'color-mix(in srgb, var(--lantern) 12%, transparent)' }}>
            <MoonStars size={19} weight="light" className="text-lantern" />
          </span>
          <div>
            <p className="text-[10px] uppercase tracking-[0.22em] text-faint">sleep rhythm</p>
            <p className="font-wizard text-lg leading-tight">Your nights</p>
          </div>
        </div>
        {pill && (
          <span className="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium"
            style={{ color: pill.color, backgroundColor: `color-mix(in srgb, ${pill.color} 14%, transparent)` }}>
            {pill.text}
          </span>
        )}
      </div>

      {/* body */}
      <div className="relative mt-4">
        {!data ? (
          <div className="grid h-32 place-items-center">
            <MotifMark size={40} />
          </div>
        ) : data.count === 0 ? (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="py-3 text-center">
            <div className="mx-auto mb-3 grid w-fit place-items-center opacity-70"><MotifMark size={36} /></div>
            <p className="font-wizard text-lg">I’m learning your nights</p>
            <p className="mx-auto mt-1.5 max-w-[16rem] text-[13px] leading-relaxed text-muted">
              Log your sleep in Life — or let a watch share it — and a quiet rhythm gathers here.
              The wizard already notices a rough streak; this is where you’ll see it.
            </p>
          </motion.div>
        ) : (
          <>
            {/* the average */}
            <div className="flex items-end gap-2">
              <span className="font-wizard text-[40px] leading-none text-ink">{avg.toFixed(1)}</span>
              <span className="pb-1 text-sm text-faint">h / night</span>
              <span className="pb-1.5 text-[11px] text-faint">· 7-night average</span>
            </div>

            {/* the bars */}
            <div className="relative mt-5" style={{ height: TRACK }}>
              {/* the rest threshold */}
              <div className="pointer-events-none absolute inset-x-0 border-t border-dashed"
                style={{ bottom: GUIDE, borderColor: 'color-mix(in srgb, var(--sage) 28%, transparent)' }} />
              <span className="pointer-events-none absolute right-0 text-[9px] uppercase tracking-wider text-faint/70"
                style={{ bottom: GUIDE + 3 }}>rest</span>

              <div className="grid h-full grid-cols-7 gap-2">
                {data.series.map((ev, i) => {
                  const tone = toneOf(ev.hours);
                  const isSel = selected === i;
                  const dim = selected != null && !isSel;
                  const last = i === data.series.length - 1;
                  return (
                    <motion.button
                      key={ev.date + i}
                      type="button"
                      onClick={() => setSelected(isSel ? null : i)}
                      whileTap={{ scale: 0.94 }}
                      className="relative flex h-full w-full items-end justify-center"
                      aria-label={`${ev.hours} hours, ${wd(ev.date)}`}
                    >
                      {last && ev.hours < 6 && (
                        <motion.span
                          className="absolute h-1.5 w-1.5 -translate-x-1/2 rounded-full"
                          style={{ left: '50%', bottom: barH(ev.hours) + 6, backgroundColor: 'var(--ember)' }}
                          animate={{ opacity: [0.4, 1, 0.4] }}
                          transition={{ duration: 2, repeat: Infinity }}
                        />
                      )}
                      <motion.span
                        className="w-full max-w-[26px] rounded-t-md"
                        style={{
                          backgroundColor: tone.bar,
                          opacity: dim ? 0.4 : 1,
                          boxShadow: isSel
                            ? `0 0 0 2px ${tone.dot}`
                            : tone.glow
                              ? `0 0 14px color-mix(in srgb, ${tone.bar} 45%, transparent)`
                              : 'none',
                        }}
                        initial={{ height: 0 }}
                        animate={{ height: barH(ev.hours) }}
                        transition={{ duration: 0.6, delay: 0.05 * i, ease: 'easeOut' }}
                      />
                    </motion.button>
                  );
                })}
              </div>
            </div>

            {/* day labels */}
            <div className="mt-2 grid grid-cols-7 gap-2">
              {data.series.map((ev, i) => (
                <span key={ev.date + i}
                  className={'text-center text-[10px] ' + (i === data.series.length - 1 ? 'font-medium text-muted' : 'text-faint')}>
                  {wd(ev.date)}
                </span>
              ))}
            </div>

            {/* selected night */}
            <AnimatePresence>
              {selected != null && data.series[selected] && (() => {
                const sel = data.series[selected];
                const t = toneOf(sel.hours);
                return (
                  <motion.div
                    key={selected}
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="mt-3 flex items-center gap-2 rounded-xl border border-line bg-bg/50 px-3 py-2 text-[13px]"
                  >
                    <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: t.dot }} />
                    <span className="text-muted">{dayLong(sel.date)}</span>
                    <span className="font-wizard text-ink">{sel.hours}h</span>
                    <span className="ml-auto text-[11px]" style={{ color: t.dot }}>{t.word}</span>
                  </motion.div>
                );
              })()}
            </AnimatePresence>

            {/* the pattern — only when the data has earned it */}
            <div className="mt-4">
              {data.pattern ? (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-start gap-2.5 rounded-xl border border-lantern/25 p-3.5"
                  style={{ backgroundColor: 'color-mix(in srgb, var(--lantern) 7%, transparent)' }}
                >
                  <Sparkle size={17} weight="fill" className="mt-0.5 shrink-0 text-lantern" />
                  <p className="font-wizard text-[15px] leading-relaxed text-ink">{data.pattern}</p>
                </motion.div>
              ) : (
                <p className="text-[12px] leading-relaxed text-faint">
                  A few more days of checking in alongside your sleep and I’ll start to see the shape — how your nights and your days rhyme.
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
