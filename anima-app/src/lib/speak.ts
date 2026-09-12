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
