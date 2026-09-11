import { lazy, Suspense, useEffect, useState } from 'react';
import {
  SunHorizon, ChatTeardrop, Plant, Sparkle, UserCircle,
} from '@phosphor-icons/react';
import { MotifMark } from '../components/brand/MotifMark';
import { subscribeOpen, subscribeTab } from '../lib/navBus';
import { ThemeToggle } from '../components/brand/ThemeToggle';
import type { IconComponent } from '../components/icons/dimensions';

// Each tab loads on first visit — the shell + Today ship first, the rest
// follow lazily, so the installed app opens fast and the bundle stays lean.
const Today = lazy(() => import('./Today').then((m) => ({ default: m.Today })));
const Companion = lazy(() => import('./Companion').then((m) => ({ default: m.Companion })));
const Life = lazy(() => import('./Life').then((m) => ({ default: m.Life })));
const Insights = lazy(() => import('./Insights').then((m) => ({ default: m.Insights })));
const You = lazy(() => import('./You').then((m) => ({ default: m.You })));

type TabId = 'today' | 'companion' | 'life' | 'insights' | 'you';

const TABS: { id: TabId; label: string; icon: IconComponent }[] = [
  { id: 'today', label: 'Today', icon: SunHorizon },
  { id: 'companion', label: 'Companion', icon: ChatTeardrop },
  { id: 'life', label: 'Life', icon: Plant },
  { id: 'insights', label: 'Insights', icon: Sparkle },
  { id: 'you', label: 'You', icon: UserCircle },
];

function TabFallback() {
  return (
    <div className="grid h-full place-items-center">
      <MotifMark size={56} />
    </div>
  );
}

export function AppShell() {
  const [active, setActive] = useState<TabId>('today');
  const [initialDim, setInitialDim] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get('connected');
    const err = params.get('error');
    if (connected) { setActive('you'); setNotice({ kind: 'ok', text: `Connected ${connected}. Motif can see your calendar now.` }); }
    else if (err) { setActive('you'); setNotice({ kind: 'err', text: `Couldn't connect: ${decodeURIComponent(err)}` }); }
    if (connected || err) window.history.replaceState({}, '', window.location.pathname);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => subscribeOpen((dim) => { setActive('life'); setInitialDim(dim); }), []);
  useEffect(() => subscribeTab((t) => setActive(t as TabId)), []);

  return (
    <div className="mx-auto flex h-[100dvh] max-w-md flex-col bg-bg text-ink">
      <header className="flex items-center justify-between px-5 pb-3 pt-6">
        <div className="flex items-center gap-2.5">
          <MotifMark size={30} />
          <span className="font-wizard text-xl tracking-tight">Motif</span>
        </div>
        <ThemeToggle />
      </header>

      <main className="flex-1 overflow-hidden px-5">
        <Suspense fallback={<TabFallback />}>
          {active === 'today' && <Today />}
          {active === 'companion' && <Companion />}
          {active === 'life' && <Life onCheckIn={() => setActive('today')} initialDim={initialDim} onDimOpened={() => setInitialDim(null)} />}
          {active === 'insights' && <Insights />}
          {active === 'you' && <You initialNotice={notice} />}
        </Suspense>
      </main>

      <nav className="flex items-center justify-around border-t border-line bg-surface px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        {TABS.map(({ id, label, icon: TabIcon }) => {
          const isActive = active === id;
          return (
            <button
              key={id}
              onClick={() => setActive(id)}
              className="flex flex-1 flex-col items-center gap-1 py-1.5"
            >
              <TabIcon size={24} weight="light" className={isActive ? 'text-lantern' : 'text-faint'} />
              <span className={`text-[10px] font-medium ${isActive ? 'text-lantern' : 'text-faint'}`}>
                {label}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
