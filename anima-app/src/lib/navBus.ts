type Listener = (dim: string) => void;
const listeners = new Set<Listener>();
export function openDimension(dim: string) { listeners.forEach((l) => l(dim)); }
export function subscribeOpen(fn: Listener) {
  listeners.add(fn);
  return () => { listeners.delete(fn); };
}

type TabListener = (tab: string) => void;
const tabListeners = new Set<TabListener>();
export function openTab(tab: string) { tabListeners.forEach((l) => l(tab)); }
export function subscribeTab(fn: TabListener) { tabListeners.add(fn); return () => { tabListeners.delete(fn); }; }
