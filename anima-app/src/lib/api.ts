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
export async function streamWizardChat(
  message: string,
  onChunk: (text: string) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/wizard/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  await readSSE(response, (data) => {
    if (data === '[DONE]') return;
    try {
      const parsed = JSON.parse(data);
      if (parsed.text) onChunk(parsed.text);
    } catch { /* ignore malformed */ }
  });
}

/** Check in with a mood: intervention data instantly, then the voice streams. */
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
export async function getLifeToday(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/life/today`);
  return res.json();
}

/** Log something toward a dimension. */
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
