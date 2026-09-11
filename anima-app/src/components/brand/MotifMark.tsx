import { useId } from 'react';
import { useReducedMotion } from 'framer-motion';

interface Props { size?: number; }

/**
 * The Motif mark — three concentric broken arcs orbiting a luminous core.
 * Geometry is taken verbatim from the source animation: outer 14s CW,
 * middle 10s CCW, inner 7s CW; 78% arcs at 0/120/240° offsets; per-layer
 * opacity 90/85/100; matching stroke-to-radius ratios. The viewBox frames
 * tightly to the artwork so the emblem holds its own beside the wordmark,
 * while the home-screen icon keeps airier padding. Pure SVG + CSS, so it
 * stays razor-sharp from 22px to the splash. One calm linear orbit on every
 * screen — the motion is the brand. Honours prefers-reduced-motion.
 */
export function MotifMark({ size = 32 }: Props) {
  const reduce = useReducedMotion();
  const spinOn = !reduce;
  const uid = useId().replace(/[:]/g, '');
  const gold = `mg-${uid}`;
  const glow = `mgg-${uid}`;
  const C = 29; // centre of the 58-unit frame

  const arcs = [
    { r: 25.4, sw: 3.30, off: 0,   dir: 'motif-cw',  ratio: 1,        op: 0.90, comet: true  },
    { r: 17.1, sw: 2.74, off: 120, dir: 'motif-ccw', ratio: 10 / 14,  op: 0.85, comet: false },
    { r: 9.3,  sw: 2.16, off: 240, dir: 'motif-cw',  ratio: 7 / 14,   op: 1.00, comet: false },
  ];

  return (
    <div style={{ width: size, height: size, lineHeight: 0 }}>
      <svg
        width={size} height={size} viewBox="0 0 58 58" fill="none"
        aria-label="Motif" role="img"
        style={{ overflow: 'visible', filter: 'drop-shadow(0 0 3px var(--amber-glow))' }}
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

        {arcs.map((a, i) => (
          <g
            key={i}
            style={{
              transformBox: 'view-box',
              transformOrigin: 'center',
              animation: spinOn ? `${a.dir} ${(14 * a.ratio).toFixed(2)}s linear infinite` : undefined,
            }}
          >
            <circle
              cx={C} cy={C} r={a.r} fill="none"
              stroke={`url(#${gold})`} strokeWidth={a.sw} strokeLinecap="round"
              strokeOpacity={a.op} pathLength={100} strokeDasharray="78 22"
              transform={`rotate(${a.off} ${C} ${C})`}
            />
            {a.comet && (
              <circle
                cx={C + a.r} cy={C} r={a.sw * 0.62} fill="var(--comet)"
                transform={`rotate(${a.off + 280.8} ${C} ${C})`}
              />
            )}
          </g>
        ))}

        <circle cx={C} cy={C} r="5" fill={`url(#${glow})`} opacity="0.55" />
        <circle cx={C} cy={C} r="1.05" fill="var(--comet)" />
      </svg>
    </div>
  );
}
