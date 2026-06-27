import { Link } from "react-router-dom";

interface Props {
  size?: number;
  textSize?: string;
  withText?: boolean;
}

export default function Logo({ size = 30, textSize = "text-[15px]", withText = true }: Props) {
  const iconSize = size * 0.78;

  return (
    <Link
      to="/"
      aria-label="Về bản đồ rủi ro EpiWeather"
      className="flex items-center gap-2.5 font-bold tracking-tight select-none rounded-md cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 hover:opacity-85 transition-opacity"
    >
      <div
        className="relative rounded-lg bg-[#1d4ed8] grid place-items-center border border-blue-200/40 overflow-hidden"
        style={{ width: size, height: size }}
      >
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
            fill="#1e3a8a"
            stroke="#ffffff"
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
        <span className={`${textSize} text-white`}>
          EpiWeather
        </span>
      )}
    </Link>
  );
}
