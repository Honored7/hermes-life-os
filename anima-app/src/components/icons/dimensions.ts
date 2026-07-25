import {
  Leaf, MoonStars, Drop, Barbell, FlowerLotus,
  Crosshair, CheckCircle, FlagBanner, Smiley,
} from '@phosphor-icons/react';
import type { CSSProperties, ComponentType } from 'react';

/**
 * Alias for a Phosphor icon component. Describes the full prop surface we
 * actually use (size, weight, className, and per-state color via style/color)
 * so the mood + dimension grids type-check under `tsc`.
 */
export type IconComponent = ComponentType<{
  size?: number | string;
  weight?: 'thin' | 'light' | 'regular' | 'bold' | 'fill' | 'duotone';
  className?: string;
  color?: string;
  style?: CSSProperties;
}>;

export type DimensionId =
  | 'nutrition' | 'sleep' | 'hydration' | 'fitness' | 'mental'
  | 'focus' | 'habits' | 'goals' | 'mood';

export const DIMENSION_ICONS: Record<DimensionId, IconComponent> = {
  nutrition: Leaf,
  sleep: MoonStars,
  hydration: Drop,
  fitness: Barbell,
  mental: FlowerLotus,
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
