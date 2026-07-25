import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { MotifMark } from './MotifMark';

/** A brief, premium launch veil: the arcs orbit while the name arrives. */
export function Splash() {
  const reduce = useReducedMotion();
  const [show, setShow] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setShow(false), reduce ? 300 : 1500);
    return () => clearTimeout(t);
  }, [reduce]);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          exit={{ opacity: 0 }}
          transition={{ duration: reduce ? 0.2 : 0.7, ease: 'easeInOut' }}
          className="fixed inset-0 z-[100] grid place-items-center"
          style={{
            background:
              'radial-gradient(120% 90% at 50% 30%, #20203f 0%, #14142b 50%, #0c0c1e 100%)',
          }}
        >
          <div className="flex flex-col items-center gap-6">
            <MotifMark size={116} />
            <motion.p
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduce ? 0 : 0.35, duration: 0.8 }}
              className="font-wizard text-3xl tracking-tight"
              style={{ color: '#F3F0E9' }}
            >
              Motif
            </motion.p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
