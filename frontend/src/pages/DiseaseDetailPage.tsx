import { useParams } from "react-router-dom";

export default function DiseaseDetailPage() {
  const { disease } = useParams<{ disease: string }>();
  const title = disease === "flu" ? "Cúm mùa (Influenza)" : "Sốt xuất huyết (Dengue)";

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{title}</h1>
      <p className="text-gray-500 mb-6">
        Trend chart, risk level và chi tiết dự báo theo quốc gia.
      </p>
      <div className="bg-white rounded-lg border border-gray-200 h-64 flex items-center justify-center">
        <span className="text-gray-400 text-sm">Recharts trend — Phase 8</span>
      </div>
    </div>
  );
}
