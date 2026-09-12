/**
 * Spoken output — browser-native, zero dependencies, no permission needed.
 *
 * Speech *output* (unlike the microphone) requires no user permission;
 * it only requires a user gesture to start, which our speaker buttons
 * always are. Chrome pauses long utterances, so text is chunked into
 * sentence-sized pieces queued in order. Tap again (or a new speak)
 * always stops what's playing first.
 */

let stopped = false;

function pickVoice(): SpeechSynthesisVoice | null {
  try {
    const voices = window.speechSynthesis.getVoices();
    if (!voices.length) return null;
    const en = voices.filter((v) => v.lang.toLowerCase().startsWith('en'));
    const pool = en.length ? en : voices;
    return (
      pool.find((v) => /female|samantha|zira|google us english/i.test(v.name)) ||
      pool.find((v) => v.localService) ||
      pool[0]
    );
  } catch {
    return null;
  }
}

function chunks(text: string): string[] {
  const parts = text
    .replace(/\s+/g, ' ')
    .match(/[^.!?…]+[.!?…]+["”)]?|\S.*$/g);
  const out = (parts || [text]).map((s) => s.trim()).filter(Boolean);
  const merged: string[] = [];
  for (const part of out) {
    const last = merged[merged.length - 1];
    if (last && last.length < 60) merged[merged.length - 1] = `${last} ${part}`;
    else merged.push(part);
  }
  return merged;
}

export function supportsSpeech(): boolean {
  try {
    return 'speechSynthesis' in window;
  } catch {
    return false;
  }
}

/**
 * Voices load asynchronously (Chrome fills the list after first paint).
 * Warm them early and await them before speaking — otherwise the first
 * tap can pick "no voice" on a device that actually has one. Resolves
 * with the voice count (0 = this device genuinely cannot speak).
 */
let warmed = false;
function warmup(): void {
  if (warmed || !supportsSpeech()) return;
  warmed = true;
  try {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
      try { window.speechSynthesis.getVoices(); } catch { /* ignore */ }
    };
  } catch { /* ignore */ }
}
warmup();

export function ensureVoices(timeoutMs = 2000): Promise<number> {
  warmup();
  if (!supportsSpeech()) return Promise.resolve(0);
  const count = () => {
    try { return window.speechSynthesis.getVoices().length; } catch { return 0; }
  };
  if (count() > 0) return Promise.resolve(count());
  return new Promise((resolve) => {
    let done = false;
    const finish = () => { if (!done) { done = true; resolve(count()); } };
    const timer = setTimeout(finish, timeoutMs);
    try {
      window.speechSynthesis.onvoiceschanged = () => { clearTimeout(timer); finish(); };
      window.speechSynthesis.getVoices();
    } catch {
      clearTimeout(timer);
      finish();
    }
  });
}

export function isSpeaking(): boolean {
  try {
    return window.speechSynthesis.speaking;
  } catch {
    return false;
  }
}

export function stopSpeak(): void {
  stopped = true;
  try {
    window.speechSynthesis.cancel();
  } catch { /* no voice — nothing to stop */ }
}

export function speak(text: string, onDone?: () => void): void {
  stopSpeak();
  const clean = (text || '').trim();
  if (!clean || !supportsSpeech()) {
    onDone?.();
    return;
  }
  stopped = false;
  const voice = pickVoice();
  const pieces = chunks(clean);
  let i = 0;
  const next = () => {
    if (stopped || i >= pieces.length) {
      if (!stopped) onDone?.();
      return;
    }
    const utter = new SpeechSynthesisUtterance(pieces[i]);
    i += 1;
    if (voice) utter.voice = voice;
    utter.rate = 0.95;
    utter.pitch = 1;
    utter.onend = next;
    utter.onerror = next;
    try {
      window.speechSynthesis.speak(utter);
    } catch {
      next();
    }
  };
  next();
}
