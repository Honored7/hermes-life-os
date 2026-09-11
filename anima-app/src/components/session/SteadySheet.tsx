import { motion } from 'framer-motion';
import { Waves, Crosshair, Sparkle } from '@phosphor-icons/react';

export type SteadyMethod = 'unwind' | 'box' | 'intention';

const OPTIONS: { id: SteadyMethod; title: string; desc: string; tag: string; Icon: typeof Waves }[] = [
  { id: 'unwind', title: 'Unwind', desc: 'A slow breath to soften the edges.', tag: '~2 min', Icon: Waves },
  { id: 'box', title: 'Box breath', desc: 'Four equal counts to steady the pulse.', tag: '~2 min', Icon: Crosshair },
  { id: 'intention', title: 'A moment of intention', desc: 'Prayer, silence, or a breath — your way.', tag: 'open', Icon: Sparkle },
];

export function SteadySheet({
  eventTitle, onPick, onClose,
}: { eventTitle: string; onPick: (m: SteadyMethod) => void; onClose: () => void }) {
  return (
    <>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose} className="fixed inset-0 z-40 bg-black/55"
      />
      <motion.div
        initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }}
        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
        className="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-md rounded-t-3xl border-t border-line bg-surface px-6 pb-9 pt-3"
      >
        <div className="mx-auto mb-5 h-1 w-10 rounded-full bg-line" />

        <p className="text-[11px] uppercase tracking-[0.25em] text-faint">steady yourself</p>
        <h3 className="mt-1 font-wizard text-2xl leading-tight">Before “{eventTitle}”</h3>
        <p className="mt-1.5 text-sm text-muted">A few minutes, your way. However you centre yourself is the right way.</p>

        <div className="mt-5 space-y-2.5">
          {OPTIONS.map(({ id, title, desc, tag, Icon }, i) => (
            <motion.button
              key={id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 + i * 0.05 }}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onPick(id)}
              className="group flex w-full items-center gap-4 rounded-card border border-line bg-bg p-4 text-left transition-colors hover:border-lantern/40"
            >
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full transition-colors"
                style={{ backgroundColor: 'color-mix(in srgb, var(--lantern) 12%, transparent)' }}>
                <Icon size={22} weight="light" className="text-lantern transition-transform group-hover:scale-110" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block font-wizard text-[17px] leading-tight">{title}</span>
                <span className="mt-0.5 block text-xs text-faint">{desc}</span>
              </span>
              <span className="shrink-0 rounded-full border border-line px-2.5 py-1 text-[10px] uppercase tracking-wider text-faint">
                {tag}
              </span>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </>
  );
}
