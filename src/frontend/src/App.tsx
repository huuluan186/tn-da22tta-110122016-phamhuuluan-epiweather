import { Navigate, Route, Routes, useMatch } from "react-router-dom";
import Footer from "./components/layout/Footer";
import TopNav from "./components/layout/TopNav";
import AnalyticsPage from "./pages/AnalyticsPage";
import DiseaseDetailPage from "./pages/DiseaseDetailPage";
import HomePage from "./pages/HomePage";
import { useUIStore } from "./store/uiStore";

export default function App() {
  // TopNav hiện tuần mới nhất từ API (latestYear/Week), không phải tuần picker.
  // Fallback về picker year/week nếu API chưa trả về.
  const latestWeek = useUIStore((s) => s.latestWeek);
  const latestYear = useUIStore((s) => s.latestYear);
  const pickerWeek = useUIStore((s) => s.week);
  const pickerYear = useUIStore((s) => s.year);
  const week = latestWeek ?? pickerWeek;
  const year = latestYear ?? pickerYear;

  // Dashboard (bản đồ) kín màn hình, panel cuộn riêng. Các trang dạng tài liệu
  // (Phân tích, Chi tiết) để cao tự giãn theo nội dung và chỉ dùng scroll của
  // document — tránh hai thanh scrollbar lồng nhau, chụp full page mới được.
  // useMatch thay pathname === "/" để tận dụng router matching của React Router
  // thay vì so sánh string thủ công — tránh false-negative khi route thay đổi.
  const isDashboard = Boolean(useMatch("/"));

  return (
    <div className="min-h-screen flex flex-col">
      <div className="sticky top-0 z-50">
        <TopNav week={week} year={year} />
      </div>
      <main
        className={`flex ${
          isDashboard ? "h-[calc(100vh-56px)] overflow-hidden" : "min-h-[calc(100vh-56px)]"
        }`}
      >
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/country" element={<Navigate to="/" replace />} />
          <Route path="/country/:iso3" element={<DiseaseDetailPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
