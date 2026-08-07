export interface QuickLog { label: string; kind: string; payload?: Record<string, any>; }
export interface LifeField { key: string; label: string; type: 'text' | 'number'; placeholder?: string; }
export interface DimModel {
  id: string;
  unit: string;
  logKind: string;
  opener: string;
  quickLogs: QuickLog[];
  fields: LifeField[];
}

export const LIFE_MODELS: Record<string, DimModel> = {
  sleep: {
    id: 'sleep', unit: 'h', logKind: 'sleep',
    opener: 'How did you sleep last night? Dreams? Restless?',
    quickLogs: [
      { label: 'Log 7.5h', kind: 'sleep', payload: { hours: 7.5, quality: 7 } },
      { label: 'Rough night (5h)', kind: 'sleep', payload: { hours: 5, quality: 4 } },
    ],
    fields: [
      { key: 'hours', label: 'Hours', type: 'number', placeholder: '7.5' },
      { key: 'quality', label: 'Quality /10', type: 'number', placeholder: '7' },
    ],
  },
  hydration: {
    id: 'hydration', unit: 'glasses', logKind: 'water',
    opener: 'How is your body feeling? Thirsty? Light? Heavy?',
    quickLogs: [
      { label: 'Log 1 glass', kind: 'water', payload: { glasses: 1 } },
      { label: 'Log 2 glasses', kind: 'water', payload: { glasses: 2 } },
    ],
    fields: [{ key: 'glasses', label: 'Glasses', type: 'number', placeholder: '8' }],
  },
  nutrition: {
    id: 'nutrition', unit: 'kcal', logKind: 'nutrition',
    opener: 'Have you eaten today? What is your body asking for?',
    quickLogs: [
      { label: 'Breakfast ~400', kind: 'nutrition', payload: { food: 'Breakfast', calories: 400, meal_time: 'breakfast' } },
      { label: 'Lunch ~600', kind: 'nutrition', payload: { food: 'Lunch', calories: 600, meal_time: 'lunch' } },
      { label: 'Dinner ~600', kind: 'nutrition', payload: { food: 'Dinner', calories: 600, meal_time: 'dinner' } },
    ],
    fields: [
      { key: 'food', label: 'What did you eat?', type: 'text', placeholder: 'Grilled salmon & rice' },
      { key: 'calories', label: 'Calories', type: 'number', placeholder: '500' },
      { key: 'meal_time', label: 'Meal', type: 'text', placeholder: 'lunch' },
    ],
  },
  fitness: {
    id: 'fitness', unit: 'min', logKind: 'fitness',
    opener: 'Has your body moved today? Even a little counts.',
    quickLogs: [
      { label: '10-min stretch', kind: 'fitness', payload: { workout_type: 'stretch', duration_min: 10 } },
      { label: '20-min walk', kind: 'fitness', payload: { workout_type: 'walk', duration_min: 20 } },
      { label: '30-min gym', kind: 'fitness', payload: { workout_type: 'gym', duration_min: 30 } },
    ],
    fields: [
      { key: 'workout_type', label: 'Type', type: 'text', placeholder: 'walk' },
      { key: 'duration_min', label: 'Minutes', type: 'number', placeholder: '20' },
    ],
  },
  focus: {
    id: 'focus', unit: 'min', logKind: 'focus',
    opener: 'How is your focus right now? Scattered? Locked in?',
    quickLogs: [
      { label: '25-min deep work', kind: 'focus', payload: { task: 'Deep work', duration_min: 25 } },
      { label: '50-min session', kind: 'focus', payload: { task: 'Deep work', duration_min: 50 } },
    ],
    fields: [
      { key: 'task', label: 'On what?', type: 'text', placeholder: 'Writing the report' },
      { key: 'duration_min', label: 'Minutes', type: 'number', placeholder: '25' },
    ],
  },
  mental: {
    id: 'mental', unit: 'stress /10', logKind: 'stress',
    opener: 'What is on your mind right now? Name it, and it gets smaller.',
    quickLogs: [
      { label: '10-min meditation', kind: 'meditation', payload: { duration_min: 10 } },
      { label: 'Log stress', kind: 'stress', payload: { score: 6 } },
      { label: 'Gratitude', kind: 'gratitude', payload: { items: ['one good thing'] } },
    ],
    fields: [
      { key: 'score', label: 'Stress /10', type: 'number', placeholder: '5' },
      { key: 'trigger', label: 'Trigger', type: 'text', placeholder: 'deadline' },
    ],
  },
  habits: {
    id: 'habits', unit: 'day streak', logKind: 'habit',
    opener: 'Which thread do you want to keep today?',
    quickLogs: [{ label: 'Mark habit done', kind: 'habit', payload: { completed: true } }],
    fields: [{ key: 'habit_name', label: 'Habit', type: 'text', placeholder: 'Morning walk' }],
  },
  goals: {
    id: 'goals', unit: '%', logKind: 'goal',
    opener: 'What are you building right now?',
    quickLogs: [{ label: 'Update progress', kind: 'goal', payload: {} }],
    fields: [
      { key: 'goal_name', label: 'Goal', type: 'text', placeholder: 'Read 12 books' },
      { key: 'progress', label: 'Progress %', type: 'number', placeholder: '40' },
      { key: 'note', label: 'Note', type: 'text', placeholder: 'Halfway there' },
    ],
  },
};
