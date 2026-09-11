import {
  Leaf, MoonStars, Drop, Barbell, FlowerLotus, Crosshair, CheckCircle, FlagBanner, Smiley,
  Wallet, UsersThree, Flask, BookOpen, Pill,
} from '@phosphor-icons/react';
import type { IconComponent } from '../components/icons/dimensions';

export type Status = 'empty' | 'tending' | 'steady' | 'thriving';
export type ActionKind = 'breathe' | 'journal' | 'checkin' | 'log';

export interface RecoveryAction { kind: ActionKind; label: string; pattern?: 'unwind' | 'box'; }

export interface DimConfig {
  id: string;
  label: string;
  icon: IconComponent;
  unit: string;
  valueKey: 'glasses' | 'hours' | 'quality' | null; // null = logged elsewhere (mood)
  target: number | null;     // a gentle aim, never a mandate
  step: number;
  accent: string;            // css color for the dimension's own hue
  copy: Record<Status, string>;
  detail: string;
  recovery: RecoveryAction[];
}

export const STATUS_COLOR: Record<Status, string> = {
  empty: 'var(--faint)',
  tending: 'var(--ember)',
  steady: 'var(--sage)',
  thriving: 'var(--lantern)',
};
export const STATUS_WORD: Record<Status, string> = {
  empty: 'a fresh thread',
  tending: 'needs tending',
  steady: 'holding steady',
  thriving: 'thriving',
};

export const DIMS: DimConfig[] = [
  {
    id: 'sleep', label: 'Sleep', icon: MoonStars, unit: 'h', valueKey: 'hours', target: 7, step: 0.5,
    accent: 'var(--mood-anxious)',
    copy: {
      empty: 'No nights logged here yet — the wizard already watches from your check-ins. Log a night and a rhythm forms.',
      tending: 'A few short nights are showing. Rest isn’t a reward for finishing everything; it’s the ground everything else stands on.',
      steady: 'You’re sleeping like someone who tends to themselves. That quiet consistency does more than you think.',
      thriving: 'Deep, restoring nights lately. Your days have somewhere to stand.',
    },
    detail: 'Here’s the shape of your rest. The wizard reads this same line when you check in — so a rough patch never goes unnoticed.',
    recovery: [{ kind: 'breathe', pattern: 'unwind', label: 'Settle into rest' }, { kind: 'journal', label: 'What’s keeping you up' }],
  },
  {
    id: 'mood', label: 'Mood & Energy', icon: Smiley, unit: '/10', valueKey: null, target: null, step: 1,
    accent: 'var(--mood-joy)',
    copy: {
      empty: 'Your feelings haven’t left a mark here yet. Naming one — even a small one — is how the companion learns your weather.',
      tending: 'The heavier feelings have been around a while. You don’t have to fix them now; just let one be seen.',
      steady: 'A balanced stretch of weather. You’ve been feeling things without being swallowed by them.',
      thriving: 'Lighter days than heavy ones lately — and you noticed the good ones, which is its own skill.',
    },
    detail: 'Your emotional weather, day by day. Tap a point to remember it; the wizard holds the whole sky.',
    recovery: [{ kind: 'checkin', label: 'Name how you feel' }, { kind: 'breathe', pattern: 'box', label: 'Two minutes to steady' }],
  },
  {
    id: 'hydration', label: 'Hydration', icon: Drop, unit: 'glasses', valueKey: 'glasses', target: 8, step: 1,
    accent: 'var(--teal)',
    copy: {
      empty: 'No water logged yet. A single glass, counted, is a perfectly good beginning.',
      tending: 'You’ve been running a little dry. Thirst is a late letter — try meeting it before it writes.',
      steady: 'Sipping along nicely. Small, steady, unglamorous — exactly what a body asks for.',
      thriving: 'Well-watered lately. Your focus and your energy both thank you, quietly.',
    },
    detail: 'Every glass, remembered. The line is the point, not the perfection.',
    recovery: [{ kind: 'log', label: 'Log a glass now' }],
  },
  {
    id: 'nutrition', label: 'Nutrition', icon: Leaf, unit: '/10', valueKey: 'quality', target: 7, step: 1,
    accent: 'var(--sage)',
    copy: {
      empty: 'Nothing logged yet. No scales, no scores — just noticing what you feed yourself, without judgment.',
      tending: 'A few light days in a row. A warm, simple meal tonight would be a kindness, not a chore.',
      steady: 'You’re eating like you care about yourself. Regular, gentle, enough.',
      thriving: 'Nourished and steady. The wizard notices the days you eat well, you feel more like you.',
    },
    detail: 'Not a diet diary — a quiet record of how you care for the body that carries you.',
    recovery: [{ kind: 'log', label: 'Log one warm meal' }, { kind: 'journal', label: 'Note a craving' }],
  },
  {
    id: 'fitness', label: 'Fitness', icon: Barbell, unit: '/10', valueKey: 'quality', target: 7, step: 1,
    accent: 'var(--mood-stressed)',
    copy: {
      empty: 'No movement logged yet. A five-minute stretch counts. The bar starts wherever you are.',
      tending: 'Movement’s been thin lately. Your mood and your sleep both lean on it more than we admit.',
      steady: 'You keep showing up for your body. That rhythm is the whole win.',
      thriving: 'Moving well lately — and your lighter days tend to follow. The connection is real.',
    },
    detail: 'Movement as medicine, not punishment. Every bit you log, the wizard remembers.',
    recovery: [{ kind: 'log', label: 'Log a small move' }, { kind: 'breathe', pattern: 'unwind', label: 'Stretch and breathe' }],
  },
  {
    id: 'mental', label: 'Mental', icon: FlowerLotus, unit: '/10', valueKey: 'quality', target: 7, step: 1,
    accent: 'var(--mood-calm)',
    copy: {
      empty: 'A blank page. Tending your mind can start as small as one slow breath, counted.',
      tending: 'The mind’s been crowded. You don’t have to clear it — just sit with it a moment, here.',
      steady: 'You’re giving your mind some air. That tending shows.',
      thriving: 'A calmer inner weather lately. The practices you keep are working.',
    },
    detail: 'Sound mental health isn’t the absence of hard feelings — it’s the tending of them. Here’s your tending.',
    recovery: [{ kind: 'breathe', pattern: 'box', label: 'A grounding breath' }, { kind: 'journal', label: 'Name what’s heavy' }],
  },
  {
    id: 'focus', label: 'Focus', icon: Crosshair, unit: '/10', valueKey: 'quality', target: 7, step: 1,
    accent: 'var(--lantern)',
    copy: {
      empty: 'Nothing logged yet. Focus isn’t a switch; it’s a small space you protect. Start by naming one thing.',
      tending: 'Focus has been slippery. Often it’s not willpower missing — it’s sleep, or noise, or too much at once.',
      steady: 'You’re holding your attention where you mean to. That’s a muscle, and you’re training it.',
      thriving: 'Clear, held focus lately. Notice what protected it — that’s your lever.',
    },
    detail: 'Where your attention goes, your days follow. Here’s the record of protecting it.',
    recovery: [{ kind: 'log', label: 'Name one focus' }, { kind: 'breathe', pattern: 'box', label: 'Clear the noise' }],
  },
  {
    id: 'habits', label: 'Habits', icon: CheckCircle, unit: '/10', valueKey: 'quality', target: 7, step: 1,
    accent: 'var(--mood-calm)',
    copy: {
      empty: 'No threads yet. A habit is just a chain of small kindnesses to your future self. Lay the first link.',
      tending: 'A thread or two has gone quiet. Missing a day doesn’t break you — the chain just rests, and waits.',
      steady: 'You’re keeping your threads. The quiet repetition is the whole magic.',
      thriving: 'Your good threads are holding. This is what becoming yourself actually looks like.',
    },
    detail: 'We don’t keep score against you here. We watch the chains grow, and we never shame a rest.',
    recovery: [{ kind: 'log', label: 'Mark today’s link' }, { kind: 'journal', label: 'What thread matters?' }],
  },
  {
    id: 'goals', label: 'Goals', icon: FlagBanner, unit: '/10', valueKey: 'quality', target: 7, step: 1,
    accent: 'var(--mood-joy)',
    copy: {
      empty: 'No goals set yet. A goal can be tiny: one walk this week. Small and real beats grand and vague.',
      tending: 'A goal’s gone a little cold. That’s information, not failure — maybe it needs a smaller next step.',
      steady: 'You’re moving toward your aims, step by unglamorous step.',
      thriving: 'Your goals are alive and moving. The wizard sees the steps, not just the summit.',
    },
    detail: 'Not a guilt-list. A place where big things get broken into the next small, kind step.',
    recovery: [{ kind: 'log', label: 'Log a small step' }, { kind: 'journal', label: 'Break it down' }],
  },
  {
    id: 'spending', label: 'Spending', icon: Wallet, unit: '$', valueKey: null, target: null, step: 1,
    accent: 'var(--sage)',
    copy: {
      empty: 'Nothing counted yet. Noticing where money goes is calm, not judgment.',
      tending: 'Spending has been running warm. Averages, not alarms — just a look, together.',
      steady: 'Money moving at its usual pace. Noticed, not judged.',
      thriving: 'Spending steady and sane lately. That quiet control is care.',
    },
    detail: 'Where it goes, without the guilt-trip. Averages over time, never a scolding.',
    recovery: [{ kind: 'log', label: 'Log what you spent' }],
  },
  {
    id: 'social', label: 'Social', icon: UsersThree, unit: 'moments', valueKey: null, target: null, step: 1,
    accent: 'var(--mood-joy)',
    copy: {
      empty: 'No moments with people logged yet. One reaching-out counts double.',
      tending: 'It’s been quiet on the people front. Loneliness shrinks the moment it’s named.',
      steady: 'You’re seeing people, in your own measure. That counts.',
      thriving: 'Good company lately — and you noticed who lifts you.',
    },
    detail: 'Who you spend time with, and how it leaves you. Notice who lifts you.',
    recovery: [{ kind: 'log', label: 'Log time with someone' }],
  },
  {
    id: 'substance', label: 'Substances', icon: Flask, unit: 'logs', valueKey: null, target: null, step: 1,
    accent: 'var(--ember)',
    copy: {
      empty: 'Nothing logged. If you ever wonder about a habit, this page only ever shows facts.',
      tending: 'A little more than usual lately. Facts, not shame — patterns you can use.',
      steady: 'An honest record, kept without flinching. That itself is steadiness.',
      thriving: 'Mindful and moderate. You’re the one deciding, and it shows.',
    },
    detail: 'A lever-view, never a lecture. How use lines up with sleep and mood.',
    recovery: [{ kind: 'journal', label: 'Note what drove it' }],
  },
  {
    id: 'reading', label: 'Reading', icon: BookOpen, unit: 'min', valueKey: null, target: 20, step: 5,
    accent: 'var(--teal)',
    copy: {
      empty: 'No pages lately. Ten quiet minutes with a book is stillness you can keep.',
      tending: 'Reading’s gone quiet. The stillness is still there, waiting.',
      steady: 'A few quiet pages here and there. Stillness, kept.',
      thriving: 'Reading well lately — protected quiet, page by page.',
    },
    detail: 'Not productivity — stillness. Minutes with a book, kept gently.',
    recovery: [{ kind: 'log', label: 'Log quiet pages' }],
  },
  {
    id: 'medication', label: 'Medication', icon: Pill, unit: 'doses', valueKey: null, target: null, step: 1,
    accent: 'var(--mood-calm)',
    copy: {
      empty: 'Nothing tracked yet. Tending yourself on schedule is care, not chore.',
      tending: 'A few missed doses. No alarm — tomorrow is a clean page.',
      steady: 'Keeping up, day by day. Faithful tending.',
      thriving: 'Steady as clockwork. Your future self thanks you.',
    },
    detail: 'Care on schedule. Adherence as self-tending — missed days get kindness, not red.',
    recovery: [{ kind: 'log', label: 'Mark today’s dose' }],
  },
];

export const DIM_BY_ID: Record<string, DimConfig> = Object.fromEntries(DIMS.map((d) => [d.id, d]));

/** Status from real data: empty / tending (neglected or struggling) / steady / thriving. */
export function statusOf(cfg: DimConfig, data: any): Status {
  const series: { date: string; value: number }[] = data?.series || [];
  const today = data?.today;
  const latest = data?.latest;
  if (!series.length && today == null && latest == null) return 'empty';
  const lastDate = series.length ? series[series.length - 1].date : null;
  const daysSince = lastDate
    ? Math.floor((Date.now() - new Date(lastDate + 'T12:00:00').getTime()) / 86400000)
    : 99;
  const cur = today ?? latest ?? 0;
  if (daysSince > 3) return 'tending';                 // neglected
  if (cfg.target != null && cur >= cfg.target) return 'thriving';
  if (cfg.target != null && cur < cfg.target * 0.6) return 'tending'; // struggling
  return 'steady';
}
