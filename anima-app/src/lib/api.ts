const API_BASE = import.meta.env.VITE_API_URL ?? '';

/**
 * Shared Server-Sent-Events reader. Every wizard stream in the app funnels
 * through this — one parser instead of four. Calls onEvent with the raw
 * payload that follows each "data: " prefix.
 */
async function readSSE(
  response: Response,
  onEvent: (data: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  if (!response.ok || !response.body) {
    throw new Error(`request failed (${response.status})`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    if (signal?.aborted) return;
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const t = line.trim();
      if (t.startsWith('data: ')) onEvent(t.slice(6));
    }
  }
}

/** Wizard free-form chat, token by token. */

export async function streamCheckIn(
  payload: { state: string; severity: number; message: string },
  handlers: {
    onMeta: (meta: any) => void;
    onToken: (text: string) => void;
    onDone: () => void;
  },
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/wizard/respond/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  let finished = false;
  const finish = () => { if (!finished) { finished = true; handlers.onDone(); } };
  await readSSE(response, (data) => {
    try {
      const ev = JSON.parse(data);
      if (ev.type === 'meta') handlers.onMeta(ev.data);
      else if (ev.type === 'token') handlers.onToken(ev.text);
      else if (ev.type === 'done') finish();
    } catch { /* ignore malformed */ }
  });
  finish();
}

/** Log a completed intervention — feeds the learning loop. */
export async function completeIntervention(
  intervention_id: number,
  state: string,
  severity_before: number,
  severity_after: number,
  effectiveness_rating?: number,
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/wizard/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      intervention_id, state, severity_before, severity_after, effectiveness_rating,
    }),
  });
  return res.json();
}

/** Freshly-spoken narration for one journey step. */
export async function streamStepNarration(
  payload: {
    protocol_id: string;
    step_number: number;
    state: string;
    severity: number;
    message: string;
  },
  handlers: { onToken: (t: string) => void; onDone: () => void },
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/wizard/narrate/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  let finished = false;
  const finish = () => { if (!finished) { finished = true; handlers.onDone(); } };
  await readSSE(response, (data) => {
    try {
      const ev = JSON.parse(data);
      if (ev.type === 'token') handlers.onToken(ev.text);
      else if (ev.type === 'done') finish();
    } catch { /* ignore malformed */ }
  });
  finish();
}

/** Today's picture across the life dimensions. */

export async function logLife(payload: {
  dimension: string;
  glasses?: number;
  hours?: number;
  quality?: number;
  note?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/log`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

/** Wins + effective interventions. */
export async function getInsights(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/insights`);
  return res.json();
}

/** The wizard's reflection over recent days. Supports abort. */
export async function streamReflection(
  onToken: (t: string) => void,
  onDone: () => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/insights/reflect/stream`, {
    method: 'POST',
    signal,
  });
  let finished = false;
  const finish = () => { if (!finished) { finished = true; onDone(); } };
  await readSSE(response, (data) => {
    try {
      const ev = JSON.parse(data);
      if (ev.type === 'token') onToken(ev.text);
      else if (ev.type === 'done') finish();
    } catch { /* ignore malformed */ }
  }, signal);
  finish();
}

// ── Calendar integrations ────────────────────────────────────────────
export async function getCalendarStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/integrations/calendar`);
  return res.json();
}

/** URL that begins the OAuth dance; navigate the whole tab to it. */
export function calendarStartUrl(provider: string, redirect: string): string {
  return `${API_BASE}/api/v1/integrations/calendar/${provider}/start?redirect=${encodeURIComponent(redirect)}`;
}

export async function disconnectCalendar(provider: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/integrations/calendar/${provider}/disconnect`, {
    method: 'POST',
  });
  return res.json();
}

export async function getCalendarEvents(limit = 5, force = false): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/integrations/calendar/events?limit=${limit}&force=${force}`);
  return res.json();
}

/** The sleep rhythm the eyes see — powers the Rhythm card. */
export async function getRhythm(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/insights/rhythm`);
  return res.json();
}

/** Mood distribution over the last week — powers the Today aura. */
export async function getMoodWeather(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/insights/mood-weather`);
  return res.json();
}

/** The bounded, grounded companion chat. Streams tokens + optional safety meta. */
export async function streamCompanionChat(
  message: string,
  onToken: (t: string) => void,
  onMeta: (ev: any) => void,
  onDone: () => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/companion/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal,
  });
  let finished = false;
  const finish = () => { if (!finished) { finished = true; onDone(); } };
  await readSSE(response, (data) => {
    try {
      const ev = JSON.parse(data);
      if (ev.type === 'token') onToken(ev.text ?? '');
      else if (ev.type === 'meta') onMeta(ev);
      else if (ev.type === 'done') finish();
    } catch { /* ignore malformed */ }
  }, signal);
  finish();
}

/** Per-dimension series + guarded cross-sight — powers the Life cards. */

export async function getJournal(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/journal`);
  return res.json();
}

export async function addJournalEntry(payload: { html: string; text: string; is_dream: boolean }): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/journal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function deleteJournalEntry(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/journal/${id}`, { method: 'DELETE' });
  return res.json();
}

/** The emotional mirror — intensity line + honest tone-shift verdict. */
export async function getMoodTrend(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/insights/mood-trend`);
  return res.json();
}

/** The You room — moments, export, wipe. */
export async function getYouMoments(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/you/moments`);
  return res.json();
}
export async function getYouExport(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/you/export`);
  return res.json();
}
export async function postYouWipe(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/you/wipe`, { method: 'POST' });
  return res.json();
}

/** Life dimensions — real stats + real logs. */
export async function getLifeStats(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/stats`);
  return res.json();
}
export async function postLifeLog(kind: string, payload: Record<string, any> = {}): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/log-dim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kind, ...payload }),
  });
  return res.json();
}

export async function getDims(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/dims`);
  return res.json();
}

export async function getSleepReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/sleep`);
  return res.json();
}

export async function getHydrationReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/hydration`);
  return res.json();
}
export async function getNutritionReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/nutrition`);
  return res.json();
}

export async function getFitnessReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/fitness`);
  return res.json();
}
export async function getFocusReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/focus`);
  return res.json();
}
export async function getMentalReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/mental`);
  return res.json();
}

/** Ambient companion: one line per dimension. Silent on failure — cards render fine without it. */
export async function fetchWhisper(dimension: string): Promise<{ dimension: string; text: string } | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/whisper?dimension=${encodeURIComponent(dimension)}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function getMirror(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/insights/mirror`);
  return res.json();
}

export async function getKeepsake(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/you/keepsake`);
  return res.json();
}

export async function getClimate(lens: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/insights/climate?lens=${lens}`);
  return res.json();
}

export async function getTodayBriefing(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/today/briefing`);
  return res.json();
}

export async function getTodayAlive(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/today/alive`);
  return res.json();
}
