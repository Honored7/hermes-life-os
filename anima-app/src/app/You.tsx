import { useEffect, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  CalendarBlank, Link as LinkIcon, LinkBreak, ArrowSquareOut, PlugsConnected,
} from '@phosphor-icons/react';
import { MotifMark } from '../components/brand/MotifMark';
import {
  getCalendarStatus, getCalendarEvents, disconnectCalendar, calendarStartUrl,
} from '../lib/api';

interface ProviderState { name: string; configured: boolean; connected: boolean; account: string; }
interface CalEvent { id: string; provider: string; title: string; start_iso: string; all_day: boolean; location: string; html_link: string; }

const META: Record<string, { label: string; blurb: string }> = {
  google: { label: 'Google Calendar', blurb: 'Gmail & Workspace events, read-only.' },
  microsoft: { label: 'Outlook', blurb: 'Personal & Microsoft 365 calendars, read-only.' },
};

function fmtTime(iso: string, allDay: boolean): string {
  const d = new Date(iso);
  if (allDay) return 'All day';
  return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}
function fmtDay(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
}

function StatusDot({ syncing }: { syncing: boolean }) {
  const reduce = useReducedMotion();
  return (
    <span className="relative grid h-2.5 w-2.5 place-items-center">
      {!reduce && syncing && (
        <motion.span className="absolute inset-0 rounded-full bg-sage"
          animate={{ scale: [1, 2.2], opacity: [0.6, 0] }}
          transition={{ duration: 1.4, repeat: Infinity }} />
      )}
      <span className="h-2 w-2 rounded-full bg-sage" />
    </span>
  );
}

function ProviderPanel({ p, onConnect, onDisconnect, busy }: {
  p: ProviderState; onConnect: () => void; onDisconnect: () => void; busy: boolean;
}) {
  const meta = META[p.name] || { label: p.name, blurb: '' };
  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ type: 'spring', stiffness: 300, damping: 24 }}
      className="relative overflow-hidden rounded-card border bg-surface p-5"
      style={{ borderColor: p.connected ? 'color-mix(in srgb, var(--sage) 40%, var(--line))' : 'var(--line)' }}
    >
      {p.connected && (
        <span className="absolute inset-y-0 left-0 w-1" style={{ background: 'var(--sage)' }} />
      )}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-full"
            style={{ backgroundColor: 'color-mix(in srgb, var(--lantern) 14%, transparent)' }}>
            <CalendarBlank size={22} weight="light" style={{ color: 'var(--lantern)' }} />
          </span>
          <div>
            <p className="font-wizard text-lg leading-tight">{meta.label}</p>
            <p className="mt-0.5 text-xs text-faint">{meta.blurb}</p>
          </div>
        </div>
        {p.connected
          ? <span className="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium text-sage"
              style={{ backgroundColor: 'color-mix(in srgb, var(--sage) 14%, transparent)' }}>
              <StatusDot syncing={busy} /> connected
            </span>
          : <span className="rounded-full border border-line px-2.5 py-1 text-[11px] text-faint">off</span>}
      </div>

      {p.connected ? (
        <div className="mt-4 flex items-center justify-between">
          <div className="min-w-0">
            <p className="truncate text-sm text-muted">{p.account || 'signed in'}</p>
            <p className="text-[11px] text-faint">read-only · you can disconnect any time</p>
          </div>
          <button onClick={onDisconnect} disabled={busy}
            className="flex shrink-0 items-center gap-1.5 rounded-full border border-line px-3.5 py-2 text-xs text-muted transition-colors hover:border-mood-angry/50 hover:text-mood-angry disabled:opacity-50">
            <LinkBreak size={15} weight="light" /> Disconnect
          </button>
        </div>
      ) : p.configured ? (
        <button onClick={onConnect} disabled={busy}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-full bg-lantern py-2.5 text-sm font-medium text-bg transition-all hover:bg-ember hover:shadow-[0_0_22px_rgba(224,162,58,0.4)] disabled:opacity-50">
          <LinkIcon size={16} weight="light" /> Connect {meta.label}
        </button>
      ) : (
        <p className="mt-4 rounded-xl border border-dashed border-line px-3 py-2.5 text-xs leading-relaxed text-faint">
          Not configured on this server yet. Add the client credentials to your environment to enable this connection.
        </p>
      )}
    </motion.div>
  );
}

export function You({ initialNotice }: { initialNotice?: { kind: 'ok' | 'err'; text: string } | null }) {
  const [status, setStatus] = useState<ProviderState[]>([]);
  const [events, setEvents] = useState<CalEvent[]>([]);
  const [meta, setMeta] = useState<any>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState(initialNotice || null);

  const load = async () => {
    try {
      const [s, e] = await Promise.all([getCalendarStatus(), getCalendarEvents(6)]);
      setStatus(s.providers || []);
      setEvents(e.events || []);
      setMeta(e.meta || null);
    } catch { /* offline / api down: leave empty */ }
  };

  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  useEffect(() => {
    if (!notice) return;
    const t = setTimeout(() => setNotice(null), 5000);
    return () => clearTimeout(t);
  }, [notice]);

  const connect = (name: string) => {
    // land back on the You tab after the dance
    window.location.href = calendarStartUrl(name, window.location.origin + '/?tab=you');
  };
  const disconnect = async (name: string) => {
    setBusy(name);
    try { await disconnectCalendar(name); await load(); }
    finally { setBusy(null); }
  };

  const anyConnected = status.some((p) => p.connected);

  return (
    <div className="relative h-full overflow-y-auto">
      {/* ambient field */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-lantern blur-[120px] opacity-10" />
        <div className="absolute right-3 top-24 opacity-[0.06]"><MotifMark size={150} /></div>
      </div>

      <div className="relative space-y-8 pb-10 pt-2">
        <header>
          <p className="text-[11px] uppercase tracking-[0.25em] text-faint">your space</p>
          <h1 className="mt-1 font-wizard text-[34px] leading-none">You</h1>
          <p className="mt-2 max-w-xs text-sm text-muted">
            The connections that let Motif see your week — and the shape of what's ahead.
          </p>
        </header>

        {notice && (
          <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 rounded-card border px-4 py-3 text-sm"
            style={{
              borderColor: notice.kind === 'ok' ? 'color-mix(in srgb, var(--sage) 40%, var(--line))' : 'color-mix(in srgb, var(--mood-angry) 40%, var(--line))',
              color: notice.kind === 'ok' ? 'var(--sage)' : 'var(--mood-angry)',
            }}>
            <PlugsConnected size={18} weight="light" /> {notice.text}
          </motion.div>
        )}

        <section className="space-y-3">
          <h2 className="text-[11px] uppercase tracking-[0.2em] text-faint">Connections</h2>
          {status.length ? status.map((p) => (
            <ProviderPanel key={p.name} p={p} busy={busy === p.name}
              onConnect={() => connect(p.name)} onDisconnect={() => disconnect(p.name)} />
          )) : (
            <p className="rounded-card border border-line bg-surface p-4 text-sm text-faint">Loading connections…</p>
          )}
        </section>

        <section className="space-y-4">
          <div className="flex items-baseline justify-between">
            <h2 className="text-[11px] uppercase tracking-[0.2em] text-faint">Next up</h2>
            {meta?.cached && <span className="text-[10px] text-faint">cached</span>}
          </div>

          {!anyConnected ? (
            <p className="rounded-card border border-line bg-surface p-5 text-sm leading-relaxed text-faint">
              Connect a calendar above and the next few days will gather here — quietly, read-only, on your device.
            </p>
          ) : events.length === 0 ? (
            <p className="rounded-card border border-line bg-surface p-5 text-sm leading-relaxed text-faint">
              Nothing on the horizon right now. A clear stretch is its own kind of gift.
            </p>
          ) : (
            <ol className="relative ml-1 space-y-1 border-l border-line pl-5">
              {events.map((e, i) => (
                <motion.li key={`${e.provider}-${e.id}`} initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                  className="relative pb-4">
                  <span className="absolute -left-[27px] top-1 grid h-3.5 w-3.5 place-items-center rounded-full border"
                    style={{ borderColor: 'var(--lantern)', backgroundColor: 'var(--bg)' }}>
                    <span className="h-1.5 w-1.5 rounded-full bg-lantern" />
                  </span>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-[15px] font-medium leading-tight">{e.title}</p>
                      <p className="mt-0.5 text-xs text-faint">
                        {fmtDay(e.start_iso)} · {fmtTime(e.start_iso, e.all_day)}
                        {e.location ? ` · ${e.location}` : ''}
                      </p>
                    </div>
                    {e.html_link && (
                      <a href={e.html_link} target="_blank" rel="noreferrer"
                        className="shrink-0 text-faint transition-colors hover:text-lantern" aria-label="Open in calendar">
                        <ArrowSquareOut size={18} weight="light" />
                      </a>
                    )}
                  </div>
                </motion.li>
              ))}
            </ol>
          )}
        </section>
      </div>
    </div>
  );
}
