import { useState } from 'react';
import {
  SunHorizon, ChatTeardrop, Plant, Sparkle, UserCircle,
} from '@phosphor-icons/react';
import { MotifMark } from '../components/brand/MotifMark';
import { ThemeToggle } from '../components/brand/ThemeToggle';
import { Today } from './Today';
import { Companion } from './Companion';
import { Life } from './Life';
import { Insights } from './Insights';
import type { IconComponent } from '../components/icons/dimensions';

type TabId = 'today' | 'companion' | 'life' | 'insights' | 'you';

const TABS: { id: TabId; label: string; icon: IconComponent }[] = [
  { id: 'today', label: 'Today', icon: SunHorizon },
  { id: 'companion', label: 'Companion', icon: ChatTeardrop },
  { id: 'life', label: 'Life', icon: Plant },
  { id: 'insights', label: 'Insights', icon: Sparkle },
  { id: 'you', label: 'You', icon: UserCircle },
];

const SCREENS: Record<TabId, boolean> = {
  today: true, companion: true, life: true, insights: true, you: false,
};

export function AppShell() {
  const [active, setActive] = useState<TabId>('today');

  return (
    <div className="mx-auto flex h-[100dvh] max-w-md flex-col bg-bg text-ink">
      <header className="flex items-center justify-between px-5 pb-3 pt-6">
        <div className="flex items-center gap-2.5">
          <MotifMark size={30} breathing />
          <span className="font-wizard text-xl tracking-tight">Motif</span>
        </div>
        <ThemeToggle />
      </header>

      <main className="flex-1 overflow-hidden px-5">
        {active === 'today' && <Today />}
        {active === 'companion' && <Companion />}
        {active === 'life' && <Life onCheckIn={() => setActive('today')} />}
        {active === 'insights' && <Insights />}
        {!SCREENS[active] && <ScreenPlaceholder name={active} />}
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

function ScreenPlaceholder({ name }: { name: TabId }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
      <MotifMark size={56} breathing />
      <p className="font-wizard text-2xl capitalize">{name}</p>
      <p className="max-w-xs text-sm leading-relaxed text-muted">
        This is where the {name} experience will live. We build it next.
      </p>
    </div>
  );
}
