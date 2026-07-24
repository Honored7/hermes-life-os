import {
  Leaf, MoonStars, Drop, Barbell, Lotus,
  Crosshair, CheckCircle, FlagBanner, Smiley,
  type Icon,
} from '@phosphor-icons/react';

export type DimensionId =
  | 'nutrition' | 'sleep' | 'hydration' | 'fitness' | 'mental'
  | 'focus' | 'habits' | 'goals' | 'mood';

export const DIMENSION_ICONS: Record<DimensionId, Icon> = {
  nutrition: Leaf,
  sleep: MoonStars,
  hydration: Drop,
  fitness: Barbell,
  mental: Lotus,
  focus: Crosshair,
  habits: CheckCircle,
  goals: FlagBanner,
  mood: Smiley,
};

export const DIMENSION_LABELS: Record<DimensionId, string> = {
  nutrition: 'Nutrition',
  sleep: 'Sleep',
  hydration: 'Hydration',
  fitness: 'Fitness',
  mental: 'Mental',
  focus: 'Focus',
  habits: 'Habits',
  goals: 'Goals',
  mood: 'Mood & Energy',
};
