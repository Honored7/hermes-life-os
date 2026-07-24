const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Stream the wizard's free-form chat reply token by token. */
export async function streamWizardChat(
  message: string,
  onChunk: (text: string) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/wizard/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (!response.ok || !response.body) throw new Error(`stream failed (${response.status})`);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const t = line.trim();
      if (!t.startsWith('data: ')) continue;
      const data = t.slice(6);
      if (data === '[DONE]') return;
      try {
        const parsed = JSON.parse(data);
        if (parsed.text) onChunk(parsed.text);
      } catch { /* ignore malformed */ }
    }
  }
}

/**
 * Check in with a mood. The intervention/session data arrives instantly
 * (onMeta), then the wizard's voice streams in (onToken).
 */
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
  if (!response.ok || !response.body) throw new Error(`check-in failed (${response.status})`);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const t = line.trim();
      if (!t.startsWith('data: ')) continue;
      const raw = t.slice(6);
      try {
        const ev = JSON.parse(raw);
        if (ev.type === 'meta') handlers.onMeta(ev.data);
        else if (ev.type === 'token') handlers.onToken(ev.text);
        else if (ev.type === 'done') { handlers.onDone(); return; }
      } catch { /* ignore malformed */ }
    }
  }
  handlers.onDone();
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
