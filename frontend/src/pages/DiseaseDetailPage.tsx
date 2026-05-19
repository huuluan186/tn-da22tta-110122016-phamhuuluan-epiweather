export default function DiseaseDetailPage() {
  return (
    <div className="flex-1 grid place-items-center bg-[var(--color-bg)] p-10 overflow-y-auto">
      <div className="max-w-[580px] w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-10">
        <h1 className="mb-3 text-2xl text-[var(--color-text-1)] font-semibold">
          Country Detail View
        </h1>
        <p className="text-[var(--color-text-2)] leading-relaxed">
          Chọn một quốc gia trên bản đồ hoặc điều hướng từ sidebar bên trái để xem chi tiết
          trend, weather drivers và lịch sử cảnh báo.
        </p>
      </div>
    </div>
  );
}
