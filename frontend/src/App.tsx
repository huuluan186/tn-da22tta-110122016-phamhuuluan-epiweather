import { Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import AnalyticsPage from "./pages/AnalyticsPage";
import DiseaseDetailPage from "./pages/DiseaseDetailPage";
import HomePage from "./pages/HomePage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/disease/:disease" element={<DiseaseDetailPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Routes>
    </Layout>
  );
}
