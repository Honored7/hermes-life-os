interface Props {
  size?: number;
  breathing?: boolean;
}

export function LanternLogo({ size = 32, breathing = false }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      className={breathing ? 'animate-breathe' : ''}
      aria-label="Anima"
    >
      {/* soft glow */}
      <circle cx="24" cy="24" r="21" fill="var(--lantern)" opacity="0.10" />
      <circle cx="24" cy="24" r="15" fill="var(--lantern)" opacity="0.10" />
      {/* crescent */}
      <path
        d="M29.5 11.5A14.5 14.5 0 1 0 29.5 36.5 12 12 0 0 1 29.5 11.5Z"
        fill="var(--lantern)"
      />
      {/* the small light */}
      <circle cx="31.5" cy="18" r="1.8" fill="var(--bg)" />
    </svg>
  );
}
