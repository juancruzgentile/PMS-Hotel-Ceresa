import {
  BedDouble,
  CalendarDays,
  ClipboardList,
  CreditCard,
  LayoutDashboard,
  Sparkles,
  Settings,
  Users,
  Wrench,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navigationItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/rooms", label: "Rooms", icon: BedDouble },
  { to: "/guests", label: "Guests", icon: Users },
  { to: "/reservations", label: "Reservations", icon: CalendarDays },
  { to: "/reception-mvp", label: "Reception MVP", icon: ClipboardList },
  { to: "/housekeeping", label: "Housekeeping", icon: Sparkles },
  { to: "/maintenance", label: "Maintenance", icon: Wrench },
  { to: "/billing", label: "Billing", icon: CreditCard },
  { to: "/system", label: "System", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand-mark">C</span>
        <span>Ceresa</span>
      </div>
      <nav className="sidebar-nav" aria-label="Main navigation">
        {navigationItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                isActive ? "sidebar-link active" : "sidebar-link"
              }
            >
              <Icon size={18} aria-hidden="true" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
