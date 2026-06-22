import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "./layouts/AppLayout";
import { BillingPage } from "@/features/billing/pages/BillingPage";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { GuestsPage } from "@/features/guests/pages/GuestsPage";
import { HousekeepingPage } from "@/features/housekeeping/pages/HousekeepingPage";
import { ReceptionMvpPage } from "@/features/reception/pages/ReceptionMvpPage";
import { ReservationsPage } from "@/features/reservations/pages/ReservationsPage";
import { RoomsPage } from "@/features/rooms/pages/RoomsPage";
import { SystemPage } from "@/features/system/pages/SystemPage";

export const router: ReturnType<typeof createBrowserRouter> =
  createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "rooms", element: <RoomsPage /> },
      { path: "guests", element: <GuestsPage /> },
      { path: "reservations", element: <ReservationsPage /> },
      { path: "reception-mvp", element: <ReceptionMvpPage /> },
      { path: "housekeeping", element: <HousekeepingPage /> },
      { path: "billing", element: <BillingPage /> },
      { path: "system", element: <SystemPage /> },
    ],
  },
  ]);
