import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { X, Play, Pause, Bell } from '@phosphor-icons/react';
import { playChime, notify, notifyPermission, notifyStatus } from '../../lib/bells';

export function FocusTimer({ minutes, onClose, onComplete }: {
  minutes: number;
  onClose: () => void;
  onComplete: (m: number) => void;
}) {
  const total = minutes * 60;
  const [left, setLeft] = useState(total);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [perm, setPerm] = useState<string>('default');
  const endRef = useRef<number | null>(null);

  useEffect(() => { setPerm(notifyStatus()); }, []);

  useEffect(() => {
    if (!running) return;
    endRef.current = Date.now() + left * 1000;
    const id = setInterval(() => {
      const l = Math.max(0, Math.round(((endRef.current as number) - Date.now()) / 1000));
      setLeft(l);
      if (l <= 0) {
        clearInterval(id);
        setRunning(false);
        setDone(true);
        playChime('done');
        notify('Focus complete', `You kept ${minutes} minutes of quiet. It counts.`);
      }
    }, 250);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running]);

  const mm = Math.floor(left / 60);
  const ss = left % 60;
  const frac = total ? left / total : 0;
  const R = 120;
  const C = 2 * Math.PI * R;

  if (done) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        className="fixed inset-0 z-[80] flex flex-col items-center justify-center bg-bg text-center">
        <div className="pointer-events-none absolute inset-0"
          style={{ background: 'radial-gradient(80% 60% at 50% 40%, color-mix(in srgb, var(--sage) 12%, transparent), transparent 70%)' }} />
        <p className="text-[40px]">🔔</p>
        <p className="mt-2 font-wizard text-[40px] leading-none text-ink">time's up</p>
        <p className="mt-3 max-w-xs font-wizard text-[15px] leading-snug text-muted">
          you kept {minutes} minutes of quiet. it counts.
        </p>
        <div className="mt-8 flex gap-3">
          <button onClick={() => onComplete(minutes)}
            className="rounded-full bg-sage px-6 py-3 text-sm font-medium text-bg transition-all hover:-translate-y-0.5">
            keep this quiet
          </button>
          <button onClick={onClose}
            className="rounded-full border border-line px-6 py-3 text-sm text-muted transition-colors hover:text-lantern">
            let it go
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-[80] flex flex-col items-center justify-center bg-bg">
      <div className="pointer-events-none absolute inset-0"
        style={{ background: 'radial-gradient(80% 60% at 50% 40%, color-mix(in srgb, var(--lantern) 10%, transparent), transparent 70%)' }} />
      <button onClick={onClose} className="absolute right-5 top-5 text-faint transition-colors hover:text-lantern">
        <X size={22} weight="light" />
      </button>

      <p className="text-[11px] uppercase tracking-[0.25em] text-faint">protected quiet</p>

      <div className="relative mt-6 grid place-items-center">
        <svg width="280" height="280" viewBox="0 0 280 280">
          <circle cx="140" cy="140" r={R} fill="none" stroke="var(--line)" strokeWidth="6" />
          <circle cx="140" cy="140" r={R} fill="none" stroke="var(--lantern)" strokeWidth="6" strokeLinecap="round"
            strokeDasharray={C} strokeDashoffset={C * (1 - frac)} transform="rotate(-90 140 140)"
            style={{ transition: 'stroke-dashoffset 0.3s linear' }} />
        </svg>
        <div className="absolute text-center">
          <p className="font-wizard text-[56px] leading-none text-ink">{mm}:{String(ss).padStart(2, '0')}</p>
          <p className="mt-1 text-xs text-faint">{running ? 'in the quiet' : 'ready when you are'}</p>
        </div>
      </div>

      <div className="mt-8 flex gap-3">
        <button onClick={() => setRunning((r) => !r)}
          className="flex items-center gap-2 rounded-full bg-lantern px-6 py-3 text-sm font-medium text-bg transition-all hover:bg-ember">
          {running ? <Pause size={16} weight="fill" /> : <Play size={16} weight="fill" />}
          {running ? 'pause' : left === total ? 'begin' : 'resume'}
        </button>
        <button onClick={onClose}
          className="rounded-full border border-line px-6 py-3 text-sm text-muted transition-colors hover:text-lantern">
          let it go
        </button>
      </div>

      {perm !== 'granted' && perm !== 'unsupported' && (
        <button onClick={async () => { const p = await notifyPermission(); setPerm(p); }}
          className="mt-6 flex items-center gap-2 text-[12px] text-faint underline-offset-2 transition-colors hover:text-lantern hover:underline">
          <Bell size={14} weight="light" /> allow the bell (notifications)
        </button>
      )}
      {perm === 'denied' && (
        <p className="mt-2 text-[11px] text-faint">notifications are blocked in your browser — the bell will still sound here.</p>
      )}
    </motion.div>
  );
}
