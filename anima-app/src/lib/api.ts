const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Stream the wizard's reflection over recent days. Supports abort. */
export async function streamReflection(
  onToken: (t: string) => void,
  onDone: () => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/insights/reflect/stream`, {
    method: 'POST',
    signal,
  });
  if (!response.ok || !response.body) throw new Error(`reflection failed (${response.status})`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    if (signal?.aborted) return;
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('
');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const t = line.trim();
      if (!t.startsWith('data: ')) continue;
      try {
        const ev = JSON.parse(t.slice(6));
        if (ev.type === 'token') onToken(ev.text);
        else if (ev.type === 'done') { onDone(); return; }
      } catch { /* ignore malformed */ }
    }
  }
  onDone();
}
