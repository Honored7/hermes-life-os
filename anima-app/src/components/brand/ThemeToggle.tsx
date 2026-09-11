import { Moon, Sun } from '@phosphor-icons/react';
import { useTheme } from '../../theme/ThemeProvider';

export function ThemeToggle() {
  const { resolved, setTheme } = useTheme();
  return (
    <button
      onClick={() => setTheme(resolved === 'dark' ? 'light' : 'dark')}
      className="rounded-full p-2 text-muted transition-colors hover:text-lantern"
      aria-label="Toggle theme"
    >
      {resolved === 'dark'
        ? <Sun size={20} weight="light" />
        : <Moon size={20} weight="light" />}
    </button>
  );
}
