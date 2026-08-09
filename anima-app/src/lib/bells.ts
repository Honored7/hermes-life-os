/**
 * Bells — the app's voice in sound and notice.
 * A soft synthesized chime (no files), and browser notifications that are
 * asked for once, gently, and used only to carry your own alarms & reminders.
 */
let ctx: AudioContext | null = null;
function ac(): AudioContext {
  if (!ctx) ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
  return ctx;
}

export function playChime(kind: 'done' | 'soft' = 'done') {
  try {
    const c = ac();
    if (c.state === 'suspended') c.resume();
    const now = c.currentTime;
    const freqs = kind === 'done' ? [523.25, 659.25, 783.99] : [659.25];
    freqs.forEach((f, i) => {
      const o = c.createOscillator();
      const g = c.createGain();
      o.type = 'sine';
      o.frequency.value = f;
      const t = now + i * 0.12;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.16, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 1.2);
      o.connect(g).connect(c.destination);
      o.start(t);
      o.stop(t + 1.3);
    });
  } catch {}
}

export function notifyPermission(): Promise<NotificationPermission | 'unsupported'> {
  if (typeof Notification === 'undefined') return Promise.resolve('unsupported');
  return Notification.requestPermission();
}

export function notifyStatus(): 'granted' | 'denied' | 'default' | 'unsupported' {
  if (typeof Notification === 'undefined') return 'unsupported';
  return Notification.permission;
}

export function notify(title: string, body: string) {
  try {
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return;
    new Notification(title, { body });
  } catch {}
}
