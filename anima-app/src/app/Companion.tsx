import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PaperPlaneTilt } from '@phosphor-icons/react';
import { MotifMark } from '../components/brand/MotifMark';
import { streamWizardChat } from '../lib/api';

interface Message {
  role: 'user' | 'wizard';
  text: string;
  streaming?: boolean;
}

const GREETING: Message = {
  role: 'wizard',
  text: "I'm here. Tell me what's on your mind — the heavy stuff, the good stuff, or nothing at all. I'm listening.",
};

const SUGGESTIONS = [
  "I'm feeling stressed",
  'I can\u2019t sleep',
  'I had a good day',
  'I feel a bit lonely',
];

export function Companion() {
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const hasUserSpoken = messages.some((m) => m.role === 'user');

  // Keep the latest message in view as the wizard speaks
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages]);

  const send = async (raw?: string) => {
    const text = (raw ?? input).trim();
    if (!text || isStreaming) return;

    setInput('');
    setMessages((prev) => [
      ...prev,
      { role: 'user', text },
      { role: 'wizard', text: '', streaming: true },
    ]);
    setIsStreaming(true);

    try {
      await streamWizardChat(text, (chunk) => {
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = {
            ...next[next.length - 1],
            text: next[next.length - 1].text + chunk,
          };
          return next;
        });
      });
    } catch {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: 'wizard',
          text: 'I\u2019m having trouble finding my voice right now. Give me a moment and try again?',
        };
        return next;
      });
    } finally {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { ...next[next.length - 1], streaming: false };
        return next;
      });
      setIsStreaming(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="relative flex h-full flex-col">
      {/* Ambient layer — the wizard's light fills the room */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-x-0 top-0 h-72 bg-[radial-gradient(ellipse_at_top,rgba(245,184,65,0.10),transparent_65%)]" />
        <div className="absolute inset-x-0 bottom-0 h-56 bg-[radial-gradient(ellipse_at_bottom,rgba(127,181,160,0.06),transparent_65%)]" />
      </div>

      {/* The wizard's presence */}
      <div className="relative flex items-center gap-3 pb-4 pt-2">
        <div className="relative">
          <MotifMark size={40} />
        </div>
        <div>
          <p className="font-wizard text-lg leading-tight">The Wizard</p>
          <p className="text-xs text-faint">
            {isStreaming ? 'speaking\u2026' : 'here with you'}
          </p>
        </div>
      </div>

      {/* Conversation */}
      <div ref={scrollRef} className="relative flex-1 space-y-6 overflow-y-auto pb-4 pr-1">
        {messages.map((msg, i) =>
          msg.role === 'wizard' ? (
            <WizardBubble key={i} msg={msg} />
          ) : (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              className="flex justify-end"
            >
              <p className="max-w-[80%] rounded-2xl rounded-br-md bg-surface-2 px-4 py-2.5 text-[15px] leading-relaxed">
                {msg.text}
              </p>
            </motion.div>
          ),
        )}
      </div>

      {/* Gentle starting points, until the first word is spoken */}
      <AnimatePresence>
        {!hasUserSpoken && (
          <motion.div
            exit={{ opacity: 0, height: 0 }}
            className="relative flex flex-wrap gap-2 pb-3"
          >
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="rounded-full border border-line bg-surface px-3.5 py-1.5 text-[13px] text-muted transition-all hover:border-lantern/50 hover:text-lantern"
              >
                {s}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="relative flex items-center gap-2 border-t border-line pt-3 pb-2"
      >
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Share what\u2019s on your mind\u2026"
          disabled={isStreaming}
          className="flex-1 rounded-full border border-line bg-surface px-4 py-2.5 text-[15px] outline-none transition-colors placeholder:text-faint focus:border-lantern/60 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isStreaming || !input.trim()}
          aria-label="Send"
          className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-lantern text-bg transition-all hover:bg-ember hover:shadow-[0_0_20px_rgba(245,184,65,0.4)] disabled:opacity-40 disabled:hover:shadow-none"
        >
          <PaperPlaneTilt size={18} weight="fill" />
        </button>
      </form>
    </div>
  );
}

function WizardBubble({ msg }: { msg: Message }) {
  const waiting = msg.streaming && !msg.text;
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="flex gap-3"
    >
      <div className="mt-1 shrink-0">
        <MotifMark size={26} />
      </div>
      <div className="min-w-0">
        {waiting ? (
          <div className="flex items-center gap-1.5 pt-2">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="h-1.5 w-1.5 rounded-full bg-lantern"
                animate={{ opacity: [0.25, 1, 0.25] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
              />
            ))}
          </div>
        ) : (
          <p className="font-wizard text-[17px] leading-relaxed text-ink">
            {msg.text}
            {msg.streaming && (
              <motion.span
                className="ml-1 inline-block h-4 w-1.5 translate-y-0.5 rounded-full bg-lantern"
                animate={{ opacity: [1, 0.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              />
            )}
          </p>
        )}
      </div>
    </motion.div>
  );
}
