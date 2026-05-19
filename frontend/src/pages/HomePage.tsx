export default function HomePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Bản đồ cảnh báo dịch bệnh</h1>
      <p className="text-gray-500 mb-6">
        Choropleth map hiển thị mức độ nguy cơ Influenza và Dengue toàn cầu.
      </p>
      <div className="bg-white rounded-lg border border-gray-200 h-[500px] flex items-center justify-center">
        <span className="text-gray-400 text-sm">Leaflet map — Phase 8</span>
      </div>
    </div>
  );
}
