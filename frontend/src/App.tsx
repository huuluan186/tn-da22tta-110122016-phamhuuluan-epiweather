import { Route, Routes } from "react-router-dom";
import TopNav from "./components/layout/TopNav";
import AnalyticsPage from "./pages/AnalyticsPage";
import DiseaseDetailPage from "./pages/DiseaseDetailPage";
import HomePage from "./pages/HomePage";
import { useUIStore } from "./store/uiStore";

export default function App() {
  const week = useUIStore((s) => s.week);
  const year = useUIStore((s) => s.year);

  return (
    <div className="grid grid-rows-[56px_1fr] h-screen overflow-hidden">
      <TopNav week={week} year={year} />
      <div className="flex overflow-hidden">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/country" element={<DiseaseDetailPage />} />
        </Routes>
      </div>
    </div>
  );
}
