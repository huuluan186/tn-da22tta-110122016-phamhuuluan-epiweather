import Logo from "./Logo";

export default function Footer() {
  return (
    <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-2)]">
      <div className="px-6 py-6 grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Brand + tagline */}
        <div className="flex flex-col gap-2.5">
          <Logo size={32} textSize="text-[16px]" />
          <p className="text-[12px] leading-relaxed text-[var(--color-text-3)] max-w-[300px]">
            Hệ thống cảnh báo nguy cơ dịch bệnh truyền nhiễm theo mùa dựa trên dữ liệu y tế và thời tiết toàn cầu.
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wider bg-gradient-to-r from-[#3b82f6] to-[#8b5cf6] text-white">
              KLTN 2026
            </span>
            <span className="text-[11px] text-[var(--color-text-3)]">v1.0.0 · 2026-W21</span>
          </div>
        </div>

        {/* Tác giả */}
        <div className="flex flex-col gap-1.5 text-[12px]">
          <h4 className="text-[10px] font-semibold tracking-[0.08em] text-[var(--color-text-3)] uppercase mb-1.5">
            Tác giả
          </h4>
          <div className="text-[var(--color-text-1)] font-semibold">Phạm Hữu Luân</div>
          <div>MSSV: <span className="text-[var(--color-text-1)] tabular-nums">110122016</span></div>
          <div>Lớp: <span className="text-[var(--color-text-1)]">DA22TTA</span></div>
          <div>GVHD: <span className="text-[var(--color-text-1)]">Phạm Thị Trúc Mai</span></div>
        </div>

        {/* Đơn vị + tech */}
        <div className="flex flex-col gap-1.5 text-[12px]">
          <h4 className="text-[10px] font-semibold tracking-[0.08em] text-[var(--color-text-3)] uppercase mb-1.5">
            Đơn vị
          </h4>
          <div className="text-[var(--color-text-1)] font-semibold">Trường Kỹ thuật và Công nghệ</div>
          <div>Đại học Trà Vinh</div>
          <div className="text-[var(--color-text-3)] leading-relaxed">
            126 Nguyễn Thiện Thành,<br />
             Phường Hòa Thuận, tỉnh Vĩnh Long
          </div>
        </div>
      </div>

      {/* Bottom bar: copyright + tech stack */}
      <div className="border-t border-[var(--color-border-soft)] px-6 py-3 flex flex-col md:flex-row items-start md:items-center justify-between gap-2 text-[11px] text-[var(--color-text-3)]">
        <div>
          © 2026 EpiWatch · Khóa luận tốt nghiệp ĐH Trà Vinh · All rights reserved.
        </div>
        <div className="flex items-center gap-3">
          <span>Powered by</span>
          <span className="text-[var(--color-text-2)]">FastAPI</span>
          <span className="opacity-40">·</span>
          <span className="text-[var(--color-text-2)]">React + Vite</span>
          <span className="opacity-40">·</span>
          <span className="text-[var(--color-text-2)]">LightGBM</span>
          <span className="opacity-40">·</span>
          <span className="text-[var(--color-text-2)]">XGBoost</span>
          <span className="opacity-40">·</span>
          <span className="text-[var(--color-text-2)]">PostgreSQL</span>
        </div>
      </div>
    </footer>
  );
}
