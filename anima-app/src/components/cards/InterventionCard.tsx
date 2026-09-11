import { motion } from 'framer-motion';
import { MotifMark } from '../brand/MotifMark';

interface Props {
  intervention: any;
  sessionConfig: any;
  onBegin: () => void;
}

export function InterventionCard({ intervention, sessionConfig, onBegin }: Props) {
  const canBreathe = !!sessionConfig?.breathing_pattern;
  const minutes = Math.max(1, Math.round(intervention.duration_seconds / 60));

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className="rounded-card border border-lantern/25 bg-surface p-5 shadow-[0_0_30px_rgba(245,184,65,0.07)]"
    >
      <div className="flex items-center gap-2.5">
        <MotifMark size={22} />
        <h3 className="font-wizard text-lg leading-tight">{intervention.name}</h3>
      </div>
      <p className="mt-1 text-xs text-faint">{intervention.family} · {minutes} min</p>

      {canBreathe ? (
        <>
          <p className="mt-3 text-sm leading-relaxed text-muted">{intervention.wizard_intro}</p>
          <button
            onClick={onBegin}
            className="mt-4 w-full rounded-full bg-lantern py-2.5 font-medium text-bg transition-all hover:bg-ember hover:shadow-[0_0_22px_rgba(245,184,65,0.45)]"
          >
            Begin the practice
          </button>
        </>
      ) : (
        <ul className="mt-3 space-y-2">
          {intervention.steps.slice(0, 4).map((s: string, i: number) => (
            <li key={i} className="flex gap-2.5 text-sm leading-relaxed text-muted">
              <span className="mt-0.5 font-wizard text-lantern">{i + 1}.</span>
              <span>{s}</span>
            </li>
          ))}
        </ul>
      )}
    </motion.div>
  );
}
