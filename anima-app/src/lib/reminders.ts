import { useEffect, useState } from 'react';
import { getHydrationReport, getFitnessReport, getNutritionReport, getFocusReport } from './api';

export type Reminder = {
  id: string; dim: string; label: string;
  mode: 'time' | 'cadence';
  at?: string; everyMin?: number;
  enabled: boolean; auto: boolean;
  cond?: string; text?: string;
};

const KEY = 'motif.reminders';

const DEFAULTS: Reminder[] = [
  { id: 'hydrate', dim: 'hydration', label: 'a glass of water', mode: 'cadence', everyMin: 120, enabled: true, auto: true, cond: 'hydration_below_goal', text: 'A glass of water would land well right now.' },
  { id: 'move', dim: 'fitness', label: 'a little movement', mode: 'cadence', everyMin: 90, enabled: true, auto: true, cond: 'no_workout_today', text: 'Your body could use a little movement — even a stretch.' },
  { id: 'winddown', dim: 'sleep', label: 'wind down', mode: 'time', at: '21:30', enabled: true, auto: true, text: 'The day is closing. A wind-down breath before bed?' },
  { id: 'lightsout', dim: 'sleep', label: 'lights out', mode: 'time', at: '22:30', enabled: true, auto: true, text: 'Lights out — tomorrow-you says thank you.' },
  { id: 'lunch', dim: 'nutrition', label: 'have you eaten?', mode: 'time', at: '13:00', enabled: true, auto: true, cond: 'no_meal_today', text: 'Midday — have you eaten something kind?' },
  { id: 'dinner', dim: 'nutrition', label: 'dinner?', mode: 'time', at: '19:30', enabled: true, auto: true, cond: 'no_meal_today', text: 'The evening plate — a good time to eat.' },
  { id: 'quiet', dim: 'focus', label: 'protect some quiet', mode: 'time', at: '10:00', enabled: true, auto: true, cond: 'no_focus_today', text: 'A block of quiet now would carry the day.' },
  { id: 'checkin', dim: 'mental', label: 'check in', mode: 'time', at: '20:00', enabled: true, auto: true, text: 'A moment to check in with yourself?' },
];

let cache: Reminder[] | null = null;
const listeners = new Set<() => void>();
function persist(rs: Reminder[]) { cache = rs; localStorage.setItem(KEY, JSON.stringify(rs)); listeners.forEach((l) => l()); }

export function getReminders(): Reminder[] {
  if (cache) return cache;
  try {
    const raw = localStorage.getItem(KEY);
    cache = raw ? (JSON.parse(raw) as Reminder[]) : DEFAULTS.map((d) => ({ ...d }));
    if (!raw) persist(cache);
  } catch { cache = DEFAULTS.map((d) => ({ ...d })); }
  return cache!;
}
export function setReminders(rs: Reminder[]) { persist(rs); }
export function updateReminder(id: string, patch: Partial<Reminder>) { persist(getReminders().map((r) => (r.id === id ? { ...r, ...patch } : r))); }
export function addReminder(r: Reminder) { persist([...getReminders(), r]); }
export function removeReminder(id: string) { persist(getReminders().filter((r) => r.id !== id)); }
export function subscribeReminders(fn: () => void) { listeners.add(fn); return () => { listeners.delete(fn); }; }

export function useReminders(): Reminder[] {
  const [rs, setRs] = useState<Reminder[]>(getReminders);
  useEffect(() => subscribeReminders(() => setRs(getReminders())), []);
  return rs;
}

// the "smart" part: only nudge when it's actually needed
export async function isRelevant(r: Reminder): Promise<boolean> {
  try {
    switch (r.cond) {
      case 'hydration_below_goal': { const rep = await getHydrationReport(); return (rep.today || 0) < (rep.goal || 8); }
      case 'no_workout_today': { const rep = await getFitnessReport(); const w = rep.week || []; const t = w[w.length - 1]; return (t?.workouts || 0) === 0; }
      case 'no_meal_today': { const rep = await getNutritionReport(); return ((rep.today || {}).meals || 0) === 0; }
      case 'no_focus_today': { const rep = await getFocusReport(); const w = rep.week || []; const t = w[w.length - 1]; return (t?.sessions || 0) === 0; }
      default: return true;
    }
  } catch { return true; }
}
