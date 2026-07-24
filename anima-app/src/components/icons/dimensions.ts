import {
  Leaf, MoonStars, Drop, Barbell, Lotus,
  Crosshair, CheckCircle, FlagBanner, Smiley,
} from '@phosphor-icons/react';
import type { ComponentType } from 'react';

export type IconComponent = ComponentType<{
  size?: number | string;
  weight?: 'thin' | 'light' | 'regular' | 'bold' | 'fill' | 'duotone';
  className?: string;
}>;

export type DimensionId =
  | 'nutrition' | 'sleep' | 'hydration' | 'fitness' | 'mental'
  | 'focus' | 'habits' | 'goals' | 'mood';

export const DIMENSION_ICONS: Record<DimensionId, IconComponent> = {
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
