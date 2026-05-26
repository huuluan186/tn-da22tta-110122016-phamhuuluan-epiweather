interface Props {
  size?: number;            // px của icon vuông; mặc định 30
  textSize?: string;        // tailwind text-* class
  withText?: boolean;       // ẩn chữ EpiWatch nếu false
}

export default function Logo({ size = 30, textSize = "text-[15px]", withText = true }: Props) {
  return (
    <div className="flex items-center gap-2.5 font-bold tracking-tight select-none">
      <div
        className="relative rounded-lg bg-gradient-to-br from-[#3b82f6] via-[#6366f1] to-[#8b5cf6] grid place-items-center shadow-[0_0_18px_rgba(99,102,241,0.45)]"
        style={{ width: size, height: size }}
      >
        <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" opacity="0.9" />
          <path d="M3 12h18" opacity="0.6" />
          <path d="M12 3a14 14 0 0 1 0 18" opacity="0.6" />
          <path d="M12 3a14 14 0 0 0 0 18" opacity="0.6" />
        </svg>
        <svg
          className="absolute -bottom-0.5 -right-0.5 bg-[#0f1117] rounded-full p-0.5"
          width={size * 0.45}
          height={size * 0.45}
          viewBox="0 0 24 24"
          fill="none"
          stroke="#22c55e"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      </div>
      {withText && (
        <span className={`${textSize} bg-gradient-to-r from-white to-[#a5b4fc] bg-clip-text text-transparent`}>
          EpiWatch
        </span>
      )}
    </div>
  );
}
