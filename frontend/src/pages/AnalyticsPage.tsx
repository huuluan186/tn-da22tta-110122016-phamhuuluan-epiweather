import { DISEASES } from "../constants";
import { useUIStore } from "../store/uiStore";

export default function AnalyticsPage() {
  const disease = useUIStore((s) => s.disease);
  const d = DISEASES.find((x) => x.id === disease)!;

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-[var(--color-bg)]">
      <div className="max-w-[1400px] mx-auto grid grid-cols-2 gap-4">
        <Card title="Epidemic Curve" full>
          <Placeholder label={`Recharts line chart — ${d.label} weekly cases`} />
        </Card>
        <Card title="Seasonal Heatmap" full>
          <Placeholder label="WHO regions × 52 weeks heatmap" />
        </Card>
        <Card title="Top Climate Drivers">
          <Placeholder label="Feature importance bar chart" />
        </Card>
        <Card title="Model Performance">
          <Placeholder label="Radar — RMSE / MAE / R² / F1 (live API)" />
        </Card>
      </div>
    </div>
  );
}

function Card({
  title,
  children,
  full,
}: {
  title: string;
  children: React.ReactNode;
  full?: boolean;
}) {
  return (
    <div
      className={`bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5 flex flex-col ${
        full ? "col-span-2" : ""
      }`}
    >
      <div className="flex justify-between items-center mb-4">
        <div className="text-[15px] font-semibold text-[var(--color-text-1)]">{title}</div>
      </div>
      {children}
    </div>
  );
}

function Placeholder({ label }: { label: string }) {
  return (
    <div className="min-h-[300px] flex-1 grid place-items-center text-[var(--color-text-3)] text-xs">
      {label}
    </div>
  );
}
