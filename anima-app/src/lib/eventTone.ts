/**
 * Event tone + presentation — the single source of truth for how the
 * horizon treats an event. Pure on purpose: no DOM, no clock side-effects
 * beyond what's passed in, so the rules stay readable and the surface can
 * never "brace" a holiday or nag a routine meeting that's hours away.
 *
 * tone:    rest    → a gift of time; never a prepare moment
 *          stress  → high-stakes; the prepare loop earns its emphasis
 *          ordinary→ everything else; a gentle, opt-in centre at most
 * cta:     what the card/row should actually offer, given the clock and
 *          whether the person already centred for it.
 */
export type Tone = 'rest' | 'stress' | 'ordinary';
export type Cta = 'emphasised' | 'gentle-stress' | 'gentle' | 'rest' | 'done' | 'none';

const STRESS = [
  'presentation', 'deadline', 'interview', 'review', 'demo', 'exam',
  'pitch', 'defense', 'defence', 'performance', 'hearing', 'keynote', 'talk',
];

const REST = [
  'holiday', 'bank holiday', 'day off', 'ooo', 'out of office', 'vacation',
  'leave', 'pto', 'birthday', 'anniversary', 'wedding', 'party', 'weekend',
  'rest day', 'mental health day', 'sabbatical', 'celebration',
];

export function toneOf(title: string): Tone {
  const t = (title || '').toLowerCase();
  if (REST.some((k) => t.includes(k))) return 'rest';
  if (STRESS.some((k) => t.includes(k))) return 'stress';
  return 'ordinary';
}

export function presentation(opts: {
  title: string;
  startMs: number;
  nowMs: number;
  prepared: boolean;
}): Cta {
  if (opts.prepared) return 'done';
  const tone = toneOf(opts.title);
  if (tone === 'rest') return 'rest';
  const mins = (opts.startMs - opts.nowMs) / 60000;
  if (tone === 'stress') return mins <= 180 ? 'emphasised' : 'gentle-stress';
  return mins <= 120 ? 'gentle' : 'none';
}
