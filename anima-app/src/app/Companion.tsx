import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PaperPlaneRight, Heart } from '@phosphor-icons/react';
import { MotifMark } from '../components/brand/MotifMark';
import { streamCompanionChat } from '../lib/api';

interface Msg { id: number; role: 'user' | 'wizard'; text: string; streaming?: boolean; safety?: boolean; }

const OPENERS = [
  'Today was heavy',
  'I can’t sleep',
  'I just need to vent',
  'What’s been helping me lately?',
];

let _id = 0;
const nextId = () => ++_id;

export function Companion() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => () => controllerRef.current?.abort(), []);

  const patchLast = (mut: (m: Msg) => Msg) =>
    setMessages((prev) => {
      const cp = [...prev];
      if (cp.length && cp[cp.length - 1].role === 'wizard') cp[cp.length - 1] = mut(cp[cp.length - 1]);
      return cp;
    });

  const send = (raw?: string) => {
    const text = (raw ?? input).trim();
    if (!text || sending) return;
    setInput('');
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    const signal = controller.signal;

    setMessages((p) => [
      ...p,
      { id: nextId(), role: 'user', text },
      { id: nextId(), role: 'wizard', text: '', streaming: true },
    ]);
    setSending(true);

    streamCompanionChat(
      text,
      (t) => { if (!signal.aborted) patchLast((m) => ({ ...m, text: m.text + t })); },
      (ev) => { if (!signal.aborted && ev?.kind === 'safety') patchLast((m) => ({ ...m, safety: true })); },
      () => { if (!signal.aborted) { patchLast((m) => ({ ...m, streaming: false })); setSending(false); } },
      signal,
    ).catch(() => {
      if (signal.aborted) return;
      patchLast((m) => ({ ...m, text: m.text || 'I lost the thread for a second. I’m still here — try me again?', streaming: false }));
      setSending(false);
    });
  };

  const empty = messages.length === 0;

  return (
    <div className="relative flex h-full flex-col">
      {/* ambient field */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-20 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-lantern blur-[120px] opacity-10" />
        {[18, 44, 70, 88].map((l, i) => (
          <span key={i} className="absolute bottom-24 h-1 w-1 rounded-full bg-lantern"
            style={{ left: `${l}%`, animation: `mote-rise ${8 + i}s ease-in ${i * 1.3}s infinite` }} />
        ))}
      </div>

      {/* the thread */}
      <div ref={scrollRef} className="relative flex-1 overflow-y-auto py-2">
        <AnimatePresence initial={false}>
          {empty ? (
            <motion.div
              key="empty"
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="flex h-full flex-col items-center justify-center px-2 text-center"
            >
              <div className="opacity-90"><MotifMark size={64} /></div>
              <h2 className="mt-5 font-wizard text-[30px] leading-tight">I’m here.</h2>
              <p className="mt-2 max-w-[17rem] text-[14px] leading-relaxed text-muted">
                Tell me what’s on your mind — or nothing at all. I’ll keep you company either way.
              </p>
              <div className="mt-7 flex max-w-xs flex-wrap justify-center gap-2">
                {OPENERS.map((o) => (
                  <button key={o} onClick={() => send(o)}
                    className="rounded-full border border-line bg-surface px-3.5 py-2 text-[13px] text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
                    {o}
                  </button>
                ))}
              </div>
            </motion.div>
          ) : (
            <div className="space-y-4">
              {messages.map((m) => (
                <motion.div
                  key={m.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={'flex ' + (m.role === 'user' ? 'justify-end' : 'justify-start')}
                >
                  {m.role === 'user' ? (
                    <div className="max-w-[82%] rounded-2xl rounded-br-md bg-surface-2 px-4 py-2.5 text-[15px] leading-relaxed text-ink">
                      {m.text}
                    </div>
                  ) : m.streaming && !m.text ? (
                    <div className="flex items-center gap-2.5 pl-1">
                      <span className="opacity-80"><MotifMark size={22} /></span>
                      <span className="flex items-center gap-1.5">
                        {[0, 1, 2].map((i) => (
                          <motion.span key={i} className="h-1.5 w-1.5 rounded-full bg-lantern"
                            animate={{ opacity: [0.25, 1, 0.25] }}
                            transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }} />
                        ))}
                      </span>
                    </div>
                  ) : m.safety ? (
                    <div className="max-w-[92%] rounded-2xl border border-lantern/30 p-4"
                      style={{ background: 'linear-gradient(160deg, color-mix(in srgb, var(--lantern) 10%, var(--surface)), var(--surface))' }}>
                      <div className="mb-2 flex items-center gap-2 text-lantern">
                        <Heart size={17} weight="fill" />
                        <span className="text-[11px] uppercase tracking-[0.2em]">you’re not alone</span>
                      </div>
                      <p className="whitespace-pre-line font-wizard text-[16px] leading-relaxed text-ink">{m.text}</p>
                    </div>
                  ) : (
                    <div className="max-w-[92%] border-l-2 border-lantern/30 pl-3.5">
                      <p className="whitespace-pre-line font-wizard text-[17px] leading-relaxed text-ink">
                        {m.text}
                        {m.streaming && (
                          <motion.span className="ml-1 inline-block h-4 w-1.5 translate-y-0.5 rounded-full bg-lantern"
                            animate={{ opacity: [1, 0.2, 1] }} transition={{ duration: 1, repeat: Infinity }} />
                        )}
                      </p>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </AnimatePresence>
      </div>

      {/* the input */}
      <div className="relative shrink-0 pb-2 pt-3">
        <div className="flex items-end gap-2 rounded-2xl border border-line bg-surface p-2 pl-4 transition-colors focus-within:border-lantern/50 focus-within:shadow-[0_0_22px_rgba(224,162,58,0.12)]">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
            }}
            rows={1}
            placeholder="Share what’s on your mind…"
            className="max-h-28 flex-1 resize-none bg-transparent py-2 text-[15px] leading-relaxed text-ink outline-none placeholder:text-faint"
          />
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => send()}
            disabled={!input.trim() || sending}
            aria-label="Send"
            className="grid h-10 w-10 shrink-0 place-items-center rounded-xl transition-all disabled:opacity-35"
            style={{
              background: input.trim() ? 'var(--lantern)' : 'transparent',
              color: input.trim() ? 'var(--bg)' : 'var(--faint)',
              boxShadow: input.trim() ? '0 0 18px rgba(224,162,58,0.35)' : 'none',
            }}
          >
            <PaperPlaneRight size={19} weight={input.trim() ? 'fill' : 'light'} />
          </motion.button>
        </div>
        <p className="mt-2 text-center text-[10px] text-faint/80">
          A companion, not a clinician · your words stay on this device
        </p>
      </div>
    </div>
  );
}
