import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  BedDouble,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  CreditCard,
  FileSearch,
  LayoutDashboard,
  Sparkles,
  Users,
  Wrench,
} from "lucide-react";

import { apiRequest } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { EmptyState } from "@/shared/components/EmptyState";
import { PageHeader } from "@/shared/components/PageHeader";

type SystemHealth = {
  app: string;
  version: string;
  status: string;
};

type ModuleStatus = {
  name: string;
  enabled: boolean;
  implemented: boolean;
  loaded: boolean;
  error: string | null;
  description: string;
};

type Room = {
  id: number;
};

type Guest = {
  id: number;
};

type Reservation = {
  id: number;
};

type OperationalSignal = {
  label: string;
  value: string;
  detail: string;
};

type LoadResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

const quickActions = [
  {
    to: "/reception-mvp",
    label: "Reception MVP",
    detail: "Run check-in/check-out flow",
    icon: ClipboardList,
  },
  {
    to: "/reservations",
    label: "Reservations",
    detail: "Search and inspect stays",
    icon: CalendarDays,
  },
  {
    to: "/guests",
    label: "Guests",
    detail: "Guest profile list",
    icon: Users,
  },
  {
    to: "/rooms",
    label: "Rooms",
    detail: "Room state board",
    icon: BedDouble,
  },
  {
    to: "/billing",
    label: "Billing",
    detail: "Accounts and balances",
    icon: CreditCard,
  },
  {
    to: "/housekeeping",
    label: "Housekeeping",
    detail: "Dirty rooms and cleaning",
    icon: Sparkles,
  },
  {
    to: "/maintenance",
    label: "Maintenance",
    detail: "Repair status overview",
    icon: Wrench,
  },
  {
    to: "/audit",
    label: "Audit",
    detail: "Reception audit events",
    icon: FileSearch,
  },
] as const;

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected API error.";
}

async function safeLoad<T>(request: Promise<T>): Promise<LoadResult<T>> {
  try {
    return {
      ok: true,
      data: await request,
    };
  } catch (error) {
    return {
      ok: false,
      error: getErrorMessage(error),
    };
  }
}

function getModuleState(moduleStatus: ModuleStatus): {
  className: string;
  label: string;
} {
  if (moduleStatus.error) {
    return {
      className: "status-pill status-dirty",
      label: "error",
    };
  }

  if (!moduleStatus.enabled) {
    return {
      className: "status-pill status-inspection",
      label: "disabled",
    };
  }

  if (moduleStatus.loaded) {
    return {
      className: "status-pill status-clean",
      label: "active",
    };
  }

  return {
    className: "status-pill status-in-progress",
    label: moduleStatus.implemented ? "not loaded" : "not implemented",
  };
}

function getCount<T>(result: LoadResult<T[]> | null): string {
  if (result === null) {
    return "-";
  }

  return result.ok ? String(result.data.length) : "not available";
}

export function SystemPage() {
  const [health, setHealth] = useState<LoadResult<SystemHealth> | null>(
    null,
  );
  const [modules, setModules] = useState<LoadResult<ModuleStatus[]> | null>(
    null,
  );
  const [rooms, setRooms] = useState<LoadResult<Room[]> | null>(null);
  const [guests, setGuests] = useState<LoadResult<Guest[]> | null>(null);
  const [reservations, setReservations] =
    useState<LoadResult<Reservation[]> | null>(null);
  const [dirtyRooms, setDirtyRooms] = useState<LoadResult<Room[]> | null>(
    null,
  );
  const [repairRooms, setRepairRooms] = useState<LoadResult<Room[]> | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  async function loadSystemOverview() {
    setIsLoading(true);
    setError(null);

    const [
      nextHealth,
      nextModules,
      nextRooms,
      nextGuests,
      nextReservations,
      nextDirtyRooms,
      nextRepairRooms,
    ] = await Promise.all([
      safeLoad<SystemHealth>(apiRequest<SystemHealth>(endpoints.system.status)),
      safeLoad<ModuleStatus[]>(
        apiRequest<ModuleStatus[]>(endpoints.system.modules),
      ),
      safeLoad<Room[]>(apiRequest<Room[]>(endpoints.rooms.list)),
      safeLoad<Guest[]>(apiRequest<Guest[]>(endpoints.guests.list)),
      safeLoad<Reservation[]>(
        apiRequest<Reservation[]>(endpoints.reservations.list),
      ),
      safeLoad<Room[]>(
        apiRequest<Room[]>(endpoints.housekeeping.dirtyRooms),
      ),
      safeLoad<Room[]>(
        apiRequest<Room[]>(endpoints.maintenance.repairRooms),
      ),
    ]);

    setHealth(nextHealth);
    setModules(nextModules);
    setRooms(nextRooms);
    setGuests(nextGuests);
    setReservations(nextReservations);
    setDirtyRooms(nextDirtyRooms);
    setRepairRooms(nextRepairRooms);

    const failedLoads = [
      nextHealth,
      nextModules,
      nextRooms,
      nextGuests,
      nextReservations,
      nextDirtyRooms,
      nextRepairRooms,
    ].filter((result) => !result.ok).length;

    if (failedLoads > 0) {
      setError(
        `${failedLoads} overview request(s) failed. Partial data is shown.`,
      );
    }

    setLastMessage(
      failedLoads === 0
        ? "System overview refreshed successfully."
        : "System overview refreshed with partial data.",
    );
    setIsLoading(false);
  }

  useEffect(() => {
    void loadSystemOverview();
    // Initial page load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const moduleRows = modules?.ok ? modules.data : [];
  const activeModules = moduleRows.filter((moduleStatus) => {
    return moduleStatus.enabled && moduleStatus.loaded && !moduleStatus.error;
  }).length;
  const disabledModules = moduleRows.filter(
    (moduleStatus) => !moduleStatus.enabled,
  ).length;
  const errorModules = moduleRows.filter(
    (moduleStatus) => moduleStatus.error,
  ).length;

  const operationalSignals: OperationalSignal[] = useMemo(
    () => [
      {
        label: "Rooms",
        value: getCount(rooms),
        detail: "GET /rooms",
      },
      {
        label: "Guests",
        value: getCount(guests),
        detail: "GET /guests",
      },
      {
        label: "Reservations",
        value: getCount(reservations),
        detail: "GET /reservations",
      },
      {
        label: "Dirty rooms",
        value: getCount(dirtyRooms),
        detail: "GET /housekeeping/dirty-rooms",
      },
      {
        label: "Repair rooms",
        value: getCount(repairRooms),
        detail: "GET /maintenance/repair-rooms",
      },
    ],
    [rooms, guests, reservations, dirtyRooms, repairRooms],
  );

  const healthLabel =
    health === null ? "-" : health.ok ? health.data.status : "unavailable";
  const healthDetail =
    health !== null && health.ok
      ? `${health.data.app} ${health.data.version}`
      : "GET /system/health";

  return (
    <>
      <PageHeader
        title="System"
        description="Operational overview of Ceresa PMS modules and MVP signals."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {lastMessage ? (
        <div className="success-banner">{lastMessage}</div>
      ) : null}

      <section className="metric-grid">
        <article className="metric-card">
          <div className="metric-card-icon">
            <LayoutDashboard size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">System health</p>
            <strong className="metric-value">{healthLabel}</strong>
            <p className="metric-detail">{healthDetail}</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <CheckCircle2 size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Active modules</p>
            <strong className="metric-value">
              {modules?.ok ? activeModules : "-"}
            </strong>
            <p className="metric-detail">Enabled and loaded</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <AlertTriangle size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Module errors</p>
            <strong className="metric-value">
              {modules?.ok ? errorModules : "-"}
            </strong>
            <p className="metric-detail">Reported by loader</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <ClipboardList size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Disabled modules</p>
            <strong className="metric-value">
              {modules?.ok ? disabledModules : "-"}
            </strong>
            <p className="metric-detail">Configured off</p>
          </div>
        </article>
      </section>

      <section className="system-layout">
        <div className="system-main">
          <section className="content-panel">
            <div className="panel-heading">
              <div>
                <h2>Module status</h2>
                <p>
                  Based on `/system/modules`. `/modules/status` is not
                  available in this backend.
                </p>
              </div>
              <button
                className="secondary-button"
                disabled={isLoading}
                onClick={() => void loadSystemOverview()}
              >
                Refresh
              </button>
            </div>

            {isLoading ? (
              <p className="muted-text">Loading system overview...</p>
            ) : modules === null || !modules.ok ? (
              <EmptyState
                title="Module status unavailable"
                message={
                  modules?.ok === false
                    ? modules.error
                    : "The module status endpoint did not return data."
                }
              />
            ) : modules.data.length === 0 ? (
              <EmptyState
                title="No modules configured"
                message="The backend returned an empty module list."
              />
            ) : (
              <div className="system-module-table">
                <div className="system-module-row system-module-head">
                  <span>Module</span>
                  <span>State</span>
                  <span>Enabled</span>
                  <span>Implemented</span>
                  <span>Loaded</span>
                  <span>Description</span>
                </div>
                {modules.data.map((moduleStatus) => {
                  const state = getModuleState(moduleStatus);

                  return (
                    <div
                      className="system-module-row"
                      key={moduleStatus.name}
                    >
                      <span>{moduleStatus.name}</span>
                      <span>
                        <span className={state.className}>{state.label}</span>
                      </span>
                      <span>{moduleStatus.enabled ? "Yes" : "No"}</span>
                      <span>
                        {moduleStatus.implemented ? "Yes" : "No"}
                      </span>
                      <span>{moduleStatus.loaded ? "Yes" : "No"}</span>
                      <span>
                        {moduleStatus.error
                          ? moduleStatus.error
                          : moduleStatus.description}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          <section className="content-panel lower-dashboard">
            <div className="panel-heading">
              <div>
                <h2>Operational signals</h2>
                <p>Simple counts from current MVP endpoints.</p>
              </div>
            </div>

            <div className="system-signal-grid">
              {operationalSignals.map((signal) => (
                <article className="inspection-card" key={signal.label}>
                  <strong>{signal.label}</strong>
                  <p className="system-signal-value">{signal.value}</p>
                  <p>{signal.detail}</p>
                </article>
              ))}
            </div>
          </section>
        </div>

        <aside className="system-sidebar">
          <section className="content-panel">
            <div className="panel-heading compact">
              <div>
                <h2>Quick access</h2>
                <p>Open the main operational MVP screens.</p>
              </div>
            </div>
            <div className="system-quick-actions">
              {quickActions.map((action) => {
                const Icon = action.icon;

                return (
                  <Link
                    className="quick-action"
                    key={action.to}
                    to={action.to}
                  >
                    <Icon size={20} aria-hidden="true" />
                    <span>
                      <strong>{action.label}</strong>
                      <small>{action.detail}</small>
                    </span>
                  </Link>
                );
              })}
            </div>
          </section>

          <section className="content-panel mvp-summary">
            <h2>Security state</h2>
            <div className="warning-banner">
              CERESA is in Phase 1 local/MVP mode. There is no real
              authentication yet.
            </div>
            <p>
              `actor_user_id` is manual traceability for audit events, not a
              login session, token, role or permission system.
            </p>
          </section>
        </aside>
      </section>
    </>
  );
}
