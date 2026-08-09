import { useEffect, useState } from 'react';
import { getKeepsake, getCalendarStatus, calendarStartUrl, disconnectCalendar } from '../lib/api';
import { CalendarBlank, Lock, Heart } from '@phosphor-icons/react';
import { MotifMark } from '../components/brand/MotifMark';

const KIND_COLOR: Record<string, string> = {
  presence: 'var(--lantern)',
  words: 'var(--mood-calm)',
  light: 'var(--sage)',
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


export function You({ initialNotice }: { initialNotice?: { kind: "ok" | "err"; text: string } | null }) {
  const [k, setK] = useState<any>(null);
  const [cal, setCal] = useState<any>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [print, setPrint] = useState<null | 'privacy' | 'terms'>(null);
  useEffect(() => { getKeepsake().then(setK).catch(() => {}); getCalendarStatus().then(setCal).catch(() => {}); }, []);
  if (!k) return <div className="grid h-60 place-items-center"><MotifMark size={56} /></div>;

  const doExport = async () => {
    try {
      const res = await fetch('/api/v1/you/export');
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'motif-you.json'; a.click();
      URL.revokeObjectURL(url);
    } catch {}
  };
  const doWipe = async () => {
    if (!confirm('Wipe everything Motif holds? This cannot be undone.')) return;
    try { await fetch('/api/v1/you/wipe', { method: 'POST' }); window.location.reload(); } catch {}
  };

  return (
    <div className="relative h-full overflow-y-auto">
      <div className="relative space-y-4 pb-10 pt-2">
        {initialNotice && (
          <div className="rounded-card border border-line bg-surface px-4 py-2 text-sm" style={{ color: initialNotice.kind === "ok" ? "var(--sage)" : "var(--mood-angry)" }}>{initialNotice.text}</div>
        )}
        <header>
          <p className="text-[11px] uppercase tracking-[0.25em] text-faint">you</p>
          <h1 className="mt-1 font-wizard text-[28px] leading-tight">What Motif holds of you</h1>
          <p className="mt-2 text-xs text-faint">{k.presence?.checkins || 0} check-ins · {k.presence?.days || 0} days kept. moments, not points.</p>
        </header>

        {(k.letter || []).length > 0 && (
          <div className="rounded-card border border-line bg-surface p-5">
            <p className="text-[11px] uppercase tracking-[0.2em] text-faint">a word from the companion</p>
            <div className="mt-2 space-y-2">
              {(k.letter || []).map((line: string, i: number) => (
                <p key={i} className="font-wizard text-[15px] leading-snug text-muted">{line}</p>
              ))}
            </div>
          </div>
        )}

        {(k.recognitions || []).length > 0 && (
          <div className="rounded-card border border-line bg-surface p-5">
            <p className="text-[11px] uppercase tracking-[0.2em] text-faint">quiet recognitions</p>
            <div className="mt-3 space-y-2">
              {(k.recognitions || []).map((r: string, i: number) => (
                <p key={i} className="flex items-start gap-2 text-sm text-muted">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-lantern" />{r}
                </p>
              ))}
            </div>
          </div>
        )}
        {(k.self_knowledge || []).length > 0 && (
          <div className="rounded-card border border-line bg-surface p-5">
            <p className="text-[11px] uppercase tracking-[0.2em] text-faint">what you've learned about yourself</p>
            <div className="mt-2 space-y-2">
              {(k.self_knowledge || []).map((s2: string, i: number) => (
                <p key={i} className="font-wizard text-[15px] leading-snug text-muted">{s2}</p>
              ))}
            </div>
          </div>
        )}

        <div className="rounded-card border border-line bg-surface p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">the kept things</p>
          {(k.moments || []).length === 0 && <p className="mt-2 text-sm text-faint">nothing kept yet. the first moment is always the quietest.</p>}
          <div className="mt-3 flex flex-wrap gap-2">
            {(k.moments || []).map((m: any, i: number) => (
              <span key={i} title={`${m.date} · ${m.text}`}
                className="grid h-9 w-9 place-items-center rounded-full"
                style={{ background: `color-mix(in srgb, ${KIND_COLOR[m.kind] || 'var(--lantern)'} 30%, transparent)` }}>
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: KIND_COLOR[m.kind] || 'var(--lantern)' }} />
              </span>
            ))}
          </div>
          <p className="mt-2 text-[10px] text-faint">each stone is a moment — a check-in, a word you wrote, a good thing you kept. hover to remember.</p>
        </div>

        {(cal?.providers || []).length > 0 && (
          <div className="rounded-card border border-line bg-surface p-5">
            <p className="text-[11px] uppercase tracking-[0.2em] text-faint">connections</p>
            <div className="mt-3 space-y-2">
              {(cal.providers || []).map((p: any) => (
                <div key={p.name} className="flex items-center justify-between gap-3 rounded-lg border border-line bg-bg p-3">
                  <div className="flex min-w-0 items-center gap-2.5">
                    <CalendarBlank size={18} weight="light" style={{ color: p.connected ? 'var(--sage)' : 'var(--faint)' }} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium capitalize text-ink">{p.name}</p>
                      <p className="truncate text-[11px] text-faint">{p.connected ? (p.account || 'connected · read-only') : p.configured ? 'not connected' : 'not configured on this server'}</p>
                    </div>
                  </div>
                  {p.connected ? (
                    <button onClick={async () => { setBusy(p.name); try { await disconnectCalendar(p.name); const c = await getCalendarStatus(); setCal(c); } finally { setBusy(null); } }}
                      disabled={busy === p.name}
                      className="shrink-0 rounded-full border border-line px-3 py-1.5 text-[11px] text-muted transition-colors hover:text-mood-angry disabled:opacity-50">
                      disconnect
                    </button>
                  ) : p.configured ? (
                    <button onClick={() => { window.location.href = calendarStartUrl(p.name, window.location.origin + '/?tab=you'); }}
                      className="shrink-0 rounded-full bg-lantern px-3 py-1.5 text-[11px] font-medium text-bg transition-all hover:bg-ember">
                      connect
                    </button>
                  ) : (
                    <span className="shrink-0 text-[11px] text-faint">—</span>
                  )}
                </div>
              ))}
            </div>
            <p className="mt-2 rounded-lg border border-line bg-bg p-3 text-[11px] leading-relaxed text-faint">
              The wearable door is ready too: when a watch enters your life, its sleep and heart-rate can flow in through Health Connect — the ingest endpoint is already waiting.
            </p>
          </div>
        )}

        <div className="rounded-card border border-line bg-surface p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">the fine print, plainly</p>
          <div className="mt-3 space-y-2">
            {([['privacy', 'Privacy — what stays on this device', Lock, PRIVACY],
               ['terms', 'Terms — the whole of them', Heart, TERMS]] as const).map(([id, title, Icon, body]) => (
              <div key={id} className="overflow-hidden rounded-lg border border-line bg-bg">
                <button onClick={() => setPrint(print === id ? null : id)} className="flex w-full items-center justify-between p-3.5 text-left">
                  <span className="flex items-center gap-2 text-sm font-medium text-ink">
                    <Icon size={16} weight="light" style={{ color: 'var(--lantern)' }} /> {title}
                  </span>
                  <span className="text-faint transition-transform" style={{ transform: print === id ? 'rotate(45deg)' : 'none' }}>+</span>
                </button>
                {print === id && (
                  <ul className="space-y-2 px-4 pb-4">
                    {(body as readonly string[]).map((line, i) => (
                      <li key={i} className="text-[12px] leading-relaxed text-muted">{line}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>


        <div className="rounded-card border border-line bg-surface p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">your data is yours</p>
          <p className="mt-2 text-xs leading-relaxed text-faint">Motif holds everything locally and shows it to no one. Take it with you, or let it all go — either way it's your call, and neither changes how you're held here.</p>
          <div className="mt-3 flex gap-2">
            <button onClick={doExport} className="rounded-full border border-line px-4 py-2 text-xs text-muted transition-colors hover:text-lantern">export it all</button>
            <button onClick={doWipe} className="rounded-full border px-4 py-2 text-xs transition-colors"
              style={{ borderColor: 'color-mix(in srgb, var(--mood-angry) 40%, var(--line))', color: 'var(--mood-angry)' }}>wipe it all</button>
          </div>
        </div>
      </div>
    </div>
  );
}
