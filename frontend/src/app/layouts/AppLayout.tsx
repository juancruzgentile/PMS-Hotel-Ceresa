import { Outlet } from "react-router-dom";

import { Sidebar } from "../navigation/Sidebar";

export function AppLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
