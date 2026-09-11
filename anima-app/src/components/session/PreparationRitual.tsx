import { useEffect, useState } from 'react';
import { motion, useReducedMotion, AnimatePresence } from 'framer-motion';
import { X, Sparkle } from '@phosphor-icons/react';

const DURATIONS = [
  { s: 30, l: '30s' },
  { s: 60, l: '1 min' },
  { s: 120, l: '2 min' },
];

/**
 * A belief-neutral preparation ritual. Motif supplies the container —
 * arrival, naming, a held moment, release — and the person supplies the
 * meaning: a prayer, a breath, a mantra, or silence. We never write the
 * sacred words; we only hold the quiet space for them.
 */
export function PreparationRitual({
  eventTitle, onDone, onClose,
}: { eventTitle: string; onDone: () => void; onClose: () => void }) {
  const reduce = useReducedMotion();
  const [idx, setIdx] = useState(0);
  const [intention, setIntention] = useState('');
  const [dur, setDur] = useState<number | null>(null);
  const [left, setLeft] = useState(0);
  const [running, setRunning] = useState(false);

  const advance = () => setIdx((i) => Math.min(i + 1, 3));

  useEffect(() => {
    if (!running || left <= 0) {
      if (running && left <= 0) { setRunning(false); advance(); }
      return;
    }
    const t = setTimeout(() => setLeft((l) => l - 1), 1000);
    return () => clearTimeout(t);
  }, [running, left]);

  const startTimer = () => { if (dur) { setLeft(dur); setRunning(true); } };
  const r = 52;
  const circ = 2 * Math.PI * r;
  const progress = dur ? left / dur : 0;

  return (
    <div className="fixed inset-0 z-50 flex flex-col"
      style={{ background: 'radial-gradient(120% 90% at 50% 25%, #20203f 0%, #14142b 52%, #0c0c1e 100%)' }}>

      {/* the held space: a slow-breathing light behind everything */}
      <div className="pointer-events-none absolute inset-0 grid place-items-center">
        <motion.div
          className="h-72 w-72 rounded-full bg-lantern/10 blur-[90px]"
          animate={reduce ? {} : { scale: [1, 1.18, 1], opacity: [0.5, 0.85, 0.5] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      <div className="relative flex items-center justify-between px-5 pt-6">
        <p className="text-[11px] uppercase tracking-[0.25em] text-faint">a moment of intention</p>
        <button onClick={onClose} className="rounded-full p-2 text-faint hover:text-lantern" aria-label="Close">
          <X size={20} weight="light" />
        </button>
      </div>

      <div className="relative flex flex-1 items-center justify-center px-6">
        <div className="w-full max-w-sm text-center">
          <AnimatePresence mode="wait">
            {idx === 0 && (
              <motion.div key="m0" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -14 }} transition={{ duration: 0.6 }}>
                <p className="font-wizard text-[30px] leading-tight">Arrive.</p>
                <p className="mx-auto mt-4 max-w-xs text-[15px] leading-relaxed text-muted">
                  Let everything else wait a moment. There is nowhere to be but here, and nothing to do but breathe once.
                </p>
                <button onClick={advance} className="mt-9 rounded-full border border-line px-7 py-2.5 text-sm text-muted transition-colors hover:border-lantern/50 hover:text-lantern">
                  I'm here
                </button>
              </motion.div>
            )}

            {idx === 1 && (
              <motion.div key="m1" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -14 }} transition={{ duration: 0.6 }}>
                <p className="font-wizard text-[26px] leading-tight">Name what's ahead.</p>
                <p className="mx-auto mt-4 max-w-xs text-[15px] leading-relaxed text-muted">
                  You're stepping toward <span className="text-ink">“{eventTitle}”</span>. Hold it gently — not as a weight, but as something you are meeting.
                </p>
                <input
                  value={intention}
                  onChange={(e) => setIntention(e.target.value)}
                  placeholder="a word or intention, if one helps (only you see this)"
                  className="mt-6 w-full rounded-xl border border-line bg-bg/60 px-4 py-3 text-center text-sm italic text-muted outline-none transition-colors placeholder:text-faint/70 focus:border-lantern/50"
                />
                <button onClick={advance} className="mt-7 rounded-full border border-line px-7 py-2.5 text-sm text-muted transition-colors hover:border-lantern/50 hover:text-lantern">
                  Continue
                </button>
              </motion.div>
            )}

            {idx === 2 && (
              <motion.div key="m2" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -14 }} transition={{ duration: 0.6 }}>
                <p className="font-wizard text-[26px] leading-tight">Your moment.</p>
                <p className="mx-auto mt-3 max-w-xs text-[15px] leading-relaxed text-muted">
                  However you centre yourself — a prayer, a breath, a few quiet words, or simply silence — this time is yours. We'll hold the space.
                </p>

                <div className="relative mx-auto mt-7 grid h-40 w-40 place-items-center">
                  {running ? (
                    <>
                      <svg width="160" height="160" className="-rotate-90">
                        <circle cx="80" cy="80" r={r} stroke="var(--surface-2)" strokeWidth="3" fill="none" />
                        <circle cx="80" cy="80" r={r} stroke="var(--lantern)" strokeWidth="3" fill="none"
                          strokeLinecap="round" strokeDasharray={circ}
                          strokeDashoffset={circ * (1 - progress)}
                          style={{ transition: 'stroke-dashoffset 1s linear' }} />
                      </svg>
                      <span className="absolute font-wizard text-3xl text-ink">{left}</span>
                    </>
                  ) : (
                    <motion.div
                      className="h-24 w-24 rounded-full border border-lantern/40 bg-lantern/10"
                      animate={reduce ? {} : { scale: [1, 1.12, 1] }}
                      transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                    />
                  )}
                </div>

                {running ? (
                  <button onClick={() => { setRunning(false); advance(); }} className="mt-7 text-xs text-faint underline-offset-4 hover:text-lantern hover:underline">
                    I'm ready now
                  </button>
                ) : (
                  <>
                    <div className="mt-6 flex justify-center gap-2">
                      {DURATIONS.map((d) => (
                        <button key={d.s} onClick={() => setDur(d.s)}
                          className="rounded-full border px-4 py-1.5 text-xs transition-all"
                          style={{
                            borderColor: dur === d.s ? 'var(--lantern)' : 'var(--line)',
                            color: dur === d.s ? 'var(--lantern)' : 'var(--muted)',
                            backgroundColor: dur === d.s ? 'color-mix(in srgb, var(--lantern) 12%, transparent)' : 'transparent',
                          }}>
                          {d.l}
                        </button>
                      ))}
                    </div>
                    <div className="mt-5 flex justify-center gap-3">
                      <button onClick={advance} className="rounded-full border border-line px-5 py-2.5 text-sm text-muted transition-colors hover:border-lantern/50 hover:text-lantern">
                        No timer
                      </button>
                      <button onClick={startTimer} disabled={!dur}
                        className="rounded-full bg-lantern px-6 py-2.5 text-sm font-medium text-bg transition-all hover:bg-ember hover:shadow-[0_0_22px_rgba(224,162,58,0.4)] disabled:opacity-40">
                        Begin
                      </button>
                    </div>
                  </>
                )}
              </motion.div>
            )}

            {idx === 3 && (
              <motion.div key="m3" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.7 }}>
                <motion.div
                  className="mx-auto mb-6 grid h-16 w-16 place-items-center"
                  initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.9 }}
                >
                  <motion.div
                    className="absolute h-16 w-16 rounded-full bg-lantern/40 blur-xl"
                    animate={reduce ? {} : { scale: [1, 1.5, 1], opacity: [0.4, 0.8, 0.4] }}
                    transition={{ duration: 3.4, repeat: Infinity }}
                  />
                  <Sparkle size={26} weight="fill" className="relative text-lantern" />
                </motion.div>
                <p className="font-wizard text-[28px] leading-tight">Carry it with you.</p>
                <p className="mx-auto mt-4 max-w-xs text-[15px] leading-relaxed text-muted">
                  Whatever you gathered here, it goes with you now. You are not walking in empty-handed.
                </p>
                {intention.trim() && (
                  <p className="mx-auto mt-4 max-w-xs font-wizard text-[16px] italic text-lantern/90">“{intention.trim()}”</p>
                )}
                <button onClick={onDone}
                  className="mt-9 w-full rounded-full bg-lantern py-3 font-medium text-bg transition-all hover:bg-ember hover:shadow-[0_0_24px_rgba(224,162,58,0.45)]">
                  I'm ready
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
