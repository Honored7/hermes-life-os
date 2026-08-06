import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smiley, Trophy, Wind, MoonStars, Feather, Moon, CalendarBlank,
  Download, Trash, Lock, Heart, Sparkle,
} from '@phosphor-icons/react';
import { MotifMark } from '../components/brand/MotifMark';
import {
  getYouMoments, getYouExport, postYouWipe,
  getCalendarStatus, calendarStartUrl, disconnectCalendar,
} from '../lib/api';

const MOMENT_ICON: Record<string, any> = {
  Smiley, Trophy, Wind, MoonStars, Feather, Moon, CalendarBlank,
};
const TONE: Record<string, string> = {
  lantern: 'var(--lantern)', sage: 'var(--sage)', calm: 'var(--mood-calm)', ember: 'var(--ember)',
};

const PRIVACY = [
  'Everything you write lives on this device. There is no account and no server holding your journal — because none exists.',
  'The companion thinks locally. It has no access to the internet, and your words are never sent away to be read.',
  'Calendar connections are read-only and removable at any time. Motif only looks at what is ahead; it never writes to your calendar.',
  'Export hands you the whole of it in one file. Wipe empties it, truly, in one tap.',
  'The only copy that ever leaves is a screenshot — and that is your choice, not ours.',
];
const TERMS = [
  'Motif is a companion, not a clinician. It does not diagnose, prescribe, or replace medical, mental-health, legal, or financial care.',
  'If you are in crisis, Motif will point you to real, human help — and so should you: findahelpline.com, or your local emergency number.',
  'Its insights are gentle reflections over your own data, not facts about you. You remain the final authority on your own life.',
  'Be kind to yourself. That is the whole terms of service.',
];

export function You({ initialNotice }: { initialNotice?: { kind: 'ok' | 'err'; text: string } | null }) {
  const [mom, setMom] = useState<any>(null);
  const [cal, setCal] = useState<any>(null);
  const [notice, setNotice] = useState(initialNotice || null);
  const [busy, setBusy] = useState<string | null>(null);
  const [wipeArmed, setWipeArmed] = useState(false);
  const [wiped, setWiped] = useState(false);
  const [print, setPrint] = useState<null | 'privacy' | 'terms'>(null);

  const load = () =>
    Promise.all([getYouMoments().catch(() => null), getCalendarStatus().catch(() => null)])
      .then(([m, c]) => { setMom(m); setCal(c); });
  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (!wipeArmed) return;
    const t = setTimeout(() => setWipeArmed(false), 4000);
    return () => clearTimeout(t);
  }, [wipeArmed]);
  useEffect(() => {
    if (!notice) return;
    const t = setTimeout(() => setNotice(null), 5000);
    return () => clearTimeout(t);
  }, [notice]);

  const c = mom?.counts || {};
  const statLine =
    (c.feel || c.nights || c.pages || c.dreams)
      ? `${c.feel || 0} check-ins · ${c.nights || 0} nights · ${(c.pages || 0) + (c.dreams || 0)} pages`
      : 'a fresh room';

  const doExport = async () => {
    setBusy('export');
    try {
      const data = await getYouExport();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `motif-export-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally { setBusy(null); }
  };

  const doWipe = async () => {
    if (!wipeArmed) { setWipeArmed(true); return; }
    setBusy('wipe');
    try {
      await postYouWipe();
      setWipeArmed(false);
      setWiped(true);
      await load();
    } finally { setBusy(null); }
  };

  return (
    <div className="relative h-full overflow-y-auto">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-lantern blur-[120px] opacity-10" />
        <div className="absolute bottom-10 right-2 opacity-[0.05]"><MotifMark size={140} /></div>
      </div>

      <div className="relative space-y-6 pb-10 pt-2">
        <header>
          <p className="text-[11px] uppercase tracking-[0.25em] text-faint">your room</p>
          <h1 className="mt-1 font-wizard text-[32px] leading-none">You, held</h1>
          <p className="mt-2 text-sm text-muted">{statLine}</p>
        </header>

        {notice && (
          <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 rounded-card border px-4 py-3 text-sm"
            style={{
              borderColor: notice.kind === 'ok' ? 'color-mix(in srgb, var(--sage) 40%, var(--line))' : 'color-mix(in srgb, var(--mood-angry) 40%, var(--line))',
              color: notice.kind === 'ok' ? 'var(--sage)' : 'var(--mood-angry)',
            }}>
            <Sparkle size={16} weight="light" /> {notice.text}
          </motion.div>
        )}

        <section>
          <h2 className="mb-1 flex items-center gap-2 font-wizard text-lg">
            <Sparkle size={19} weight="light" className="text-lantern" /> Moments
          </h2>
          <p className="mb-3 text-[12px] leading-relaxed text-faint">
            Not points, not streaks. Kept things — the quiet proof you have been tending yourself.
          </p>
          {(mom?.moments?.length ?? 0) > 0 ? (
            <div className="space-y-2.5">
              {mom.moments.map((m: any, i: number) => {
                const Icon = MOMENT_ICON[m.icon] || Sparkle;
                const tone = TONE[m.tone] || 'var(--lantern)';
                return (
                  <motion.div key={m.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.06 }} whileHover={{ y: -2 }}
                    className="flex items-start gap-3 rounded-card border border-line bg-surface p-4">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full"
                      style={{ backgroundColor: `color-mix(in srgb, ${tone} 14%, transparent)` }}>
                      <Icon size={19} weight="light" style={{ color: tone }} />
                    </span>
                    <p className="font-wizard text-[15px] leading-snug text-ink">{m.text}</p>
                  </motion.div>
                );
              })}
            </div>
          ) : (
            <p className="rounded-card border border-line bg-surface p-4 text-sm leading-relaxed text-faint">
              No moments kept yet. That is not a lack — it is a beginning.
            </p>
          )}
          {mom?.next && (
            <p className="mt-3 rounded-card border border-lantern/25 p-3.5 font-wizard text-[14px] leading-snug text-muted"
              style={{ backgroundColor: 'color-mix(in srgb, var(--lantern) 6%, transparent)' }}>
              {mom.next}
            </p>
          )}
        </section>

        <section>
          <h2 className="mb-3 font-wizard text-lg">Connections</h2>
          <div className="space-y-2.5">
            {(cal?.providers || []).map((p: any) => (
              <div key={p.name} className="flex items-center justify-between gap-3 rounded-card border border-line bg-surface p-4">
                <div className="flex min-w-0 items-center gap-3">
                  <CalendarBlank size={20} weight="light" className={p.connected ? 'text-sage' : 'text-faint'} />
                  <div className="min-w-0">
                    <p className="text-[14px] font-medium capitalize">{p.name}</p>
                    <p className="truncate text-[11px] text-faint">
                      {p.connected ? (p.account || 'connected · read-only') : p.configured ? 'not connected' : 'not configured on this server'}
                    </p>
                  </div>
                </div>
                {p.connected ? (
                  <button onClick={async () => { setBusy(p.name); try { await disconnectCalendar(p.name); await load(); } finally { setBusy(null); } }}
                    disabled={busy === p.name}
                    className="shrink-0 rounded-full border border-line px-3.5 py-1.5 text-[12px] text-muted transition-colors hover:border-mood-angry/50 hover:text-mood-angry disabled:opacity-50">
                    Disconnect
                  </button>
                ) : p.configured ? (
                  <button onClick={() => { window.location.href = calendarStartUrl(p.name, window.location.origin + '/?tab=you'); }}
                    className="shrink-0 rounded-full bg-lantern px-3.5 py-1.5 text-[12px] font-medium text-bg transition-all hover:bg-ember">
                    Connect
                  </button>
                ) : (
                  <span className="shrink-0 text-[11px] text-faint">—</span>
                )}
              </div>
            ))}
            <p className="rounded-card border border-line bg-surface p-3.5 text-[12px] leading-relaxed text-faint">
              The wearable door is ready too: when a watch enters your life, its sleep and heart-rate can flow in through Health Connect — the ingest endpoint is already waiting.
            </p>
          </div>
        </section>

        <section>
          <h2 className="mb-1 font-wizard text-lg">Your data, in your hands</h2>
          <p className="mb-3 text-[12px] leading-relaxed text-faint">
            Local-first, always. The whole of it is yours to take — or to erase.
          </p>
          <div className="grid grid-cols-2 gap-2.5">
            <button onClick={doExport} disabled={busy === 'export'}
              className="flex items-center justify-center gap-2 rounded-card border border-line bg-surface p-4 text-sm text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern disabled:opacity-50">
              <Download size={17} weight="light" /> {busy === 'export' ? 'Gathering…' : 'Export everything'}
            </button>
            <button onClick={doWipe} disabled={busy === 'wipe'}
              className="flex items-center justify-center gap-2 rounded-card border p-4 text-sm transition-all hover:-translate-y-0.5 disabled:opacity-50"
              style={{
                borderColor: wipeArmed ? 'var(--mood-angry)' : 'var(--line)',
                color: wipeArmed ? 'var(--mood-angry)' : 'var(--muted)',
                backgroundColor: wipeArmed ? 'color-mix(in srgb, var(--mood-angry) 10%, var(--surface))' : 'var(--surface)',
              }}>
              <Trash size={17} weight="light" />
              {busy === 'wipe' ? 'Erasing…' : wipeArmed ? 'Tap again to erase everything' : 'Wipe it all'}
            </button>
          </div>
          <AnimatePresence>
            {wiped && (
              <motion.p initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="mt-3 text-[13px] text-sage">
                Your journal is a blank page again. The room is quiet, and it is still yours.
              </motion.p>
            )}
          </AnimatePresence>
        </section>

        <section>
          <h2 className="mb-3 font-wizard text-lg">The fine print, plainly</h2>
          <div className="space-y-2.5">
            {([['privacy', 'Privacy — what stays on this device', Lock, PRIVACY],
               ['terms', 'Terms — the whole of them', Heart, TERMS]] as const).map(([id, title, Icon, body]) => (
              <div key={id} className="overflow-hidden rounded-card border border-line bg-surface">
                <button onClick={() => setPrint(print === id ? null : id)}
                  className="flex w-full items-center justify-between p-4 text-left">
                  <span className="flex items-center gap-2.5 text-[14px] font-medium text-ink">
                    <Icon size={17} weight="light" className="text-lantern" /> {title}
                  </span>
                  <motion.span animate={{ rotate: print === id ? 45 : 0 }} className="text-faint">+</motion.span>
                </button>
                <AnimatePresence initial={false}>
                  {print === id && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                      <ul className="space-y-2.5 px-4 pb-4">
                        {body.map((line, i) => (
                          <li key={i} className="text-[13px] leading-relaxed text-muted">{line}</li>
                        ))}
                      </ul>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </section>

        <footer className="pt-2 text-center">
          <div className="mx-auto grid w-fit place-items-center opacity-80"><MotifMark size={40} /></div>
          <p className="mt-3 font-wizard text-[14px] text-muted">
            Motif — the patterns of a life, held gently.
          </p>
          <p className="mt-1 text-[11px] leading-relaxed text-faint">
            Three arcs in orbit: your days, your nights, your moods —<br />separate lines that turn out to be one motion.
          </p>
          <p className="mt-2 text-[10px] text-faint/70">v0.5 · built with you</p>
        </footer>
      </div>
    </div>
  );
}
