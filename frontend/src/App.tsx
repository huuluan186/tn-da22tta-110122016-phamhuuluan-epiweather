import { Route, Routes } from "react-router-dom";
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

  return (
    <div className="min-h-screen flex flex-col">
      <div className="sticky top-0 z-50">
        <TopNav week={week} year={year} />
      </div>
      <main className="flex h-[calc(100vh-56px)] overflow-hidden">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/country/:iso3" element={<DiseaseDetailPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
