import { useNavigate } from "react-router-dom";
import AlertsSidebar from "../components/alerts/AlertsSidebar";
import MapLegend from "../components/map/MapLegend";
import WorldMap from "../components/map/WorldMap";
import RiskMapSidebar from "../components/sidebar/RiskMapSidebar";
import { DISEASES } from "../constants";
import { useUIStore } from "../store/uiStore";

export default function HomePage() {
  const navigate = useNavigate();
  const { disease, setDisease, year, setYear, week, setWeek, regions, toggleRegion } =
    useUIStore();
  const activeDisease = DISEASES.find((d) => d.id === disease)!;

  return (
    <div className="flex flex-1 min-h-0 overflow-hidden">
      <RiskMapSidebar
        disease={disease}
        setDisease={setDisease}
        year={year}
        setYear={setYear}
        week={week}
        setWeek={setWeek}
        regions={regions}
        toggleRegion={toggleRegion}
      />

      <div className="flex-1 relative bg-[var(--color-bg)] overflow-hidden flex flex-col">
        <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-5 py-3.5 z-[3] pointer-events-none">
          <div className="pointer-events-auto">
            <h2 className="m-0 text-[15px] font-semibold">
              Global Risk Map · {activeDisease.label}
            </h2>
            <p className="m-0 mt-0.5 text-xs text-[var(--color-text-2)]">
              W{String(week).padStart(2, "0")} · {year}
              {regions.length ? ` · ${regions.join(", ")}` : ""}
            </p>
          </div>
        </div>

        <WorldMap disease={disease} week={week} onCountrySelect={() => navigate("/country")} />
        <MapLegend />
      </div>

      <AlertsSidebar week={week} />
    </div>
  );
}
