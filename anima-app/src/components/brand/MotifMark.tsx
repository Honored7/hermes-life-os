import { useId } from 'react';
import { useReducedMotion } from 'framer-motion';

interface Props {
  size?: number;
  /** gentle scale pulse (the mark is "alive") */
  breathing?: boolean;
  /** orbit the arcs */
  spin?: boolean;
  /** seconds for the outer arc's full orbit (bigger = calmer) */
  spinSpeed?: number;
}

/**
 * The Motif mark: three concentric broken arcs orbiting a glowing core.
 * Pure SVG + CSS — no Lottie runtime — so it stays sharp at any size.
 * Rotation directions/speeds mirror the original splash animation:
 * outer CW, middle CCW, inner CW.
 */
export function MotifMark({ size = 32, breathing = false, spin = false, spinSpeed = 14 }: Props) {
  const reduce = useReducedMotion();
  const spinOn = spin && !reduce;
  const breatheOn = breathing && !reduce;
  const uid = useId().replace(/[:]/g, '');
  const gold = `mg-${uid}`;
  const glow = `mgg-${uid}`;

  const arcs = [
    { r: 42, sw: 5, off: 0, dir: 'motif-cw', ratio: 1, comet: true },
    { r: 28, sw: 4, off: 120, dir: 'motif-ccw', ratio: 0.714, comet: false },
    { r: 15, sw: 3.4, off: 240, dir: 'motif-cw', ratio: 0.5, comet: false },
  ];

  return (
    <div
      className={breatheOn ? 'animate-breathe' : ''}
      style={{ width: size, height: size, lineHeight: 0 }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        aria-label="Motif"
        role="img"
        style={{ filter: 'drop-shadow(0 0 3px var(--amber-glow))' }}
      >
        <defs>
          <linearGradient id={gold} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--amber-light)" />
            <stop offset="55%" stopColor="var(--lantern)" />
            <stop offset="100%" stopColor="var(--amber-deep)" />
          </linearGradient>
          <radialGradient id={glow}>
            <stop offset="0%" stopColor="var(--amber-light)" stopOpacity="0.9" />
            <stop offset="100%" stopColor="var(--amber-light)" stopOpacity="0" />
          </radialGradient>
        </defs>

        {arcs.map((a, i) => {
          const c = 2 * Math.PI * a.r;
          const dash = `${(0.78 * c).toFixed(2)} ${(0.22 * c).toFixed(2)}`;
          return (
            <g
              key={i}
              style={{
                transformBox: 'view-box',
                transformOrigin: 'center',
                animation: spinOn
                  ? `${a.dir} ${(spinSpeed * a.ratio).toFixed(2)}s linear infinite`
                  : undefined,
              }}
            >
              <circle
                cx="50" cy="50" r={a.r}
                fill="none"
                stroke={`url(#${gold})`}
                strokeWidth={a.sw}
                strokeLinecap="round"
                strokeDasharray={dash}
                transform={`rotate(${a.off} 50 50)`}
              />
              {a.comet && (
                <circle
                  cx={50 + a.r} cy="50" r={a.sw * 0.6}
                  fill="var(--comet)"
                  transform={`rotate(${a.off} 50 50)`}
                />
              )}
            </g>
          );
        })}

        <circle cx="50" cy="50" r="9" fill={`url(#${glow})`} />
        <circle cx="50" cy="50" r="1.9" fill="var(--comet)" />
      </svg>
    </div>
  );
}
