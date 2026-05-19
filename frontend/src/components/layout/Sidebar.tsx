import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { label: "Bản đồ cảnh báo", to: "/" },
  { label: "Cúm mùa (Flu)", to: "/disease/flu" },
  { label: "Sốt xuất huyết", to: "/disease/dengue" },
  { label: "Phân tích", to: "/analytics" },
] as const;

export default function Sidebar() {
  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div className="h-14 flex items-center px-4 border-b border-gray-200">
        <span className="font-semibold text-gray-800">EpiWeather</span>
      </div>
      <nav className="flex-1 py-4">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `block px-4 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-blue-50 text-blue-700 font-medium"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
