import { useState } from 'react';
import {
  SunHorizon, ChatTeardrop, Plant, Sparkle, UserCircle,
  type Icon,
} from '@phosphor-icons/react';
import { LanternLogo } from '../components/brand/LanternLogo';
import { ThemeToggle } from '../components/brand/ThemeToggle';

type TabId = 'today' | 'companion' | 'life' | 'insights' | 'you';

const TABS: { id: TabId; label: string; icon: Icon }[] = [
  { id: 'today', label: 'Today', icon: SunHorizon },
  { id: 'companion', label: 'Companion', icon: ChatTeardrop },
  { id: 'life', label: 'Life', icon: Plant },
  { id: 'insights', label: 'Insights', icon: Sparkle },
  { id: 'you', label: 'You', icon: UserCircle },
];

export function AppShell() {
  const [active, setActive] = useState<TabId>('today');

  return (
    <div className="mx-auto flex h-[100dvh] max-w-md flex-col bg-bg text-ink">
      {/* Header */}
      <header className="flex items-center justify-between px-5 pb-3 pt-6">
        <div className="flex items-center gap-2.5">
          <LanternLogo size={30} breathing />
          <span className="font-wizard text-xl tracking-tight">Anima</span>
        </div>
        <ThemeToggle />
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto px-5">
        <ScreenPlaceholder name={active} />
      </main>

      {/* Bottom navigation */}
      <nav className="flex items-center justify-around border-t border-line bg-surface px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        {TABS.map(({ id, label, icon: TabIcon }) => {
          const isActive = active === id;
          return (
            <button
              key={id}
              onClick={() => setActive(id)}
              className="flex flex-1 flex-col items-center gap-1 py-1.5"
            >
              <TabIcon
                size={24}
                weight="light"
                className={isActive ? 'text-lantern' : 'text-faint'}
              />
              <span
                className={`text-[10px] font-medium ${
                  isActive ? 'text-lantern' : 'text-faint'
                }`}
              >
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
      <LanternLogo size={56} breathing />
      <p className="font-wizard text-2xl capitalize">{name}</p>
      <p className="max-w-xs text-sm leading-relaxed text-muted">
        This is where the {name} experience will live. We build it next.
      </p>
    </div>
  );
}
