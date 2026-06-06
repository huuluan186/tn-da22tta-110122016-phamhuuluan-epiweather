interface Props {
  size?: number;
  textSize?: string;
  withText?: boolean;
}

export default function Logo({ size = 30, textSize = "text-[15px]", withText = true }: Props) {
  const iconSize = size * 0.78;

  return (
    <div className="flex items-center gap-2.5 font-bold tracking-tight select-none">
      <div
        className="relative rounded-lg bg-[#111827] grid place-items-center shadow-[0_0_18px_rgba(20,184,166,0.32)] ring-1 ring-white/10 overflow-hidden"
        style={{ width: size, height: size }}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_28%_18%,rgba(34,197,94,0.34),transparent_36%),linear-gradient(135deg,#0f766e_0%,#2563eb_52%,#4f46e5_100%)]" />
        <svg
          width={iconSize}
          height={iconSize}
          viewBox="0 0 64 64"
          fill="none"
          aria-hidden="true"
          className="relative"
        >
          <path
            d="M32 6.5 52 14v15.7c0 12.5-8.1 22.9-20 27.8-11.9-4.9-20-15.3-20-27.8V14l20-7.5Z"
            fill="rgba(15,23,42,0.64)"
            stroke="rgba(255,255,255,0.86)"
            strokeWidth="3"
            strokeLinejoin="round"
          />
          <circle cx="32" cy="29" r="14" stroke="#bfdbfe" strokeWidth="2.5" />
          <path
            d="M18 29h28M32 15c4.1 3.7 6.2 8.3 6.2 14S36.1 39.3 32 43M32 15c-4.1 3.7-6.2 8.3-6.2 14S27.9 39.3 32 43"
            stroke="#93c5fd"
            strokeWidth="2"
            strokeLinecap="round"
            opacity="0.82"
          />
          <path
            d="M16 42h8l3.6-8.2 7.2 15.1 3.7-7H48"
            stroke="#34d399"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle cx="48" cy="42" r="4.4" fill="#ef4444" stroke="white" strokeWidth="2.4" />
        </svg>
      </div>
      {withText && (
        <span className={`${textSize} bg-gradient-to-r from-white via-[#bfdbfe] to-[#5eead4] bg-clip-text text-transparent`}>
          EpiWatch
        </span>
      )}
    </div>
  );
}
