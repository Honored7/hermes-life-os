import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, BellRinging, X, Trash } from '@phosphor-icons/react';
import { playChime, notify, notifyPermission, notifyStatus } from '../../lib/bells';
import { useReminders, updateReminder, removeReminder, addReminder, isRelevant } from '../../lib/reminders';

const KEY = 'motif.bells';
const LAST = 'motif.bells.last';
type Cfg = { enabled: boolean; quietFrom: number; quietTo: number };
const DEF: Cfg = { enabled: false, quietFrom: 22, quietTo: 7 };
function loadCfg(): Cfg { try { return { ...DEF, ...JSON.parse(localStorage.getItem(KEY) || '{}') }; } catch { return DEF; } }
function loadLast(): Record<string, number> { try { return JSON.parse(localStorage.getItem(LAST) || '{}'); } catch { return {}; } }
function saveLast(l: Record<string, number>) { localStorage.setItem(LAST, JSON.stringify(l)); }
function sameDay(ts: number) { return new Date(ts).toDateString() === new Date().toDateString(); }
const DIMS = ['hydration', 'sleep', 'nutrition', 'fitness', 'focus', 'mental', 'habits', 'goals'];

export function Bells() {
  const [open, setOpen] = useState(false);
  const [cfg, setCfg] = useState<Cfg>(loadCfg);
  const [perm, setPerm] = useState<string>(notifyStatus());
  const [toast, setToast] = useState<string | null>(null);
  const reminders = useReminders();

  useEffect(() => { localStorage.setItem(KEY, JSON.stringify(cfg)); }, [cfg]);

  useEffect(() => {
    const tick = async () => {
      const c = loadCfg();
      if (!c.enabled) return;
      const now = new Date();
      const h = now.getHours();
      if (h >= c.quietFrom || h < c.quietTo) return;
      const hhmm = `${String(h).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      const last = loadLast();
      for (const r of getRemindersSafe()) {
        if (!r.enabled) continue;
        let due = false;
        if (r.mode === 'cadence') due = Date.now() - (last[r.id] || 0) >= (r.everyMin || 120) * 60e3;
        else due = !(last[r.id] && sameDay(last[r.id])) && hhmm === (r.at || '');
        if (!due) continue;
        last[r.id] = Date.now(); saveLast(last);
        if (!(await isRelevant(r))) continue; // smart: unneeded nudges stay silent
        playChime('soft');
        setToast(r.text || r.label);
        notify('Motif', r.text || r.label);
        break;
      }
    };
    tick();
    const id = setInterval(tick, 30e3);
    return () => clearInterval(id);
  }, []);
  function getRemindersSafe() { return reminders; }

  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(null), 5000); return () => clearTimeout(t); }, [toast]);

  return (
    <>
      <button onClick={() => setOpen(true)} title="bells & reminders"
        className="fixed right-4 top-4 z-[60] grid h-10 w-10 place-items-center rounded-full border border-line bg-surface text-faint transition-all hover:-translate-y-0.5 hover:text-lantern">
        {cfg.enabled ? <BellRinging size={18} weight="light" style={{ color: 'var(--lantern)' }} /> : <Bell size={18} weight="light" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] flex items-end justify-center bg-bg/70 sm:items-center" onClick={() => setOpen(false)}>
            <motion.div onClick={(e) => e.stopPropagation()} initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 40, opacity: 0 }}
              className="max-h-[85vh] w-full max-w-md overflow-y-auto rounded-t-card border border-line bg-surface p-5 sm:rounded-card">
              <div className="flex items-center justify-between">
                <p className="text-[11px] uppercase tracking-[0.2em] text-faint">bells & reminders</p>
                <button onClick={() => setOpen(false)} className="text-faint hover:text-lantern"><X size={18} weight="light" /></button>
              </div>
              <p className="mt-2 font-wizard text-[14px] leading-snug text-muted">The companion nudges, never nags. Bells live inside each dimension — smart ones stay silent when they're not needed.</p>

              <label className="mt-4 flex items-center justify-between rounded-card border border-line bg-bg px-4 py-3">
                <span className="text-sm text-ink">bells on</span>
                <input type="checkbox" checked={cfg.enabled} onChange={(e) => setCfg((c) => ({ ...c, enabled: e.target.checked }))} className="h-4 w-4 accent-[var(--lantern)]" />
              </label>
              {perm !== 'granted' && perm !== 'unsupported' && (
                <button onClick={async () => { const p = await notifyPermission(); setPerm(p); }}
                  className="mt-2 w-full rounded-full border border-line px-4 py-2 text-xs text-muted transition-colors hover:text-lantern">
                  allow notifications — the bell reaches you even in another tab
                </button>
              )}

              <div className="mt-4 space-y-4">
                {DIMS.map((dim) => {
                  const rs = reminders.filter((r) => r.dim === dim);
                  if (rs.length === 0) return null;
                  return (
                    <div key={dim}>
                      <p className="mb-1.5 text-[10px] uppercase tracking-[0.2em] text-faint">{dim}</p>
                      <div className="space-y-1.5">
                        {rs.map((r) => (
                          <div key={r.id} className="flex items-center justify-between gap-2 rounded-card border border-line bg-bg px-3 py-2">
                            <button onClick={() => updateReminder(r.id, { enabled: !r.enabled })} className="flex min-w-0 flex-1 items-center gap-2 text-left">
                              <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: r.enabled ? 'var(--lantern)' : 'var(--line)' }} />
                              <span className="min-w-0 truncate text-sm" style={{ color: r.enabled ? 'var(--ink)' : 'var(--faint)' }}>{r.label}</span>
                              <span className="shrink-0 text-[10px] text-faint">{r.mode === 'time' ? r.at : `every ${Math.round((r.everyMin || 0) / 60)}h`}{r.auto ? ' · auto' : ''}</span>
                            </button>
                            <button onClick={() => removeReminder(r.id)} className="shrink-0 text-faint transition-colors hover:text-mood-angry"><Trash size={13} weight="light" /></button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="mt-4 text-[11px] text-faint">quiet hours {cfg.quietFrom}:00 – {cfg.quietTo}:00 — no bells while you rest. Add or tune bells inside each dimension's card.</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {toast && (
          <motion.div key={toast} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="fixed bottom-6 left-1/2 z-[80] -translate-x-1/2 rounded-full px-5 py-2.5 text-sm font-medium shadow-xl"
            style={{ background: 'var(--lantern)', color: 'var(--bg)' }}>
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// a compact bell row embedded inside each dimension card
export function DimBells({ dim }: { dim: string }) {
  const rs = useReminders().filter((r) => r.dim === dim);
  return (
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <Bell size={13} weight="light" className="text-faint" />
      {rs.map((r) => (
        <button key={r.id} onClick={() => updateReminder(r.id, { enabled: !r.enabled })}
          className="rounded-full border px-2.5 py-1 text-[10px] transition-all"
          style={{
            borderColor: r.enabled ? 'color-mix(in srgb, var(--lantern) 50%, var(--line))' : 'var(--line)',
            color: r.enabled ? 'var(--lantern)' : 'var(--faint)',
            opacity: r.enabled ? 1 : 0.6,
          }}>
          {r.label} · {r.mode === 'time' ? r.at : `every ${Math.round((r.everyMin || 0) / 60)}h`}
        </button>
      ))}
      <button onClick={() => addReminder({ id: `${dim}-${Date.now()}`, dim, label: 'a gentle nudge', mode: 'cadence', everyMin: 120, enabled: true, auto: false })}
        className="rounded-full border border-dashed border-line px-2.5 py-1 text-[10px] text-faint transition-colors hover:text-lantern">
        + bell
      </button>
    </div>
  );
}
