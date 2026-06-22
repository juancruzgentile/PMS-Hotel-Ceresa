import {
  AlertTriangle,
  BedDouble,
  CalendarCheck2,
  CreditCard,
  Sparkles,
  Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { PageHeader } from "@/shared/components/PageHeader";

const dashboardMetrics = [
  {
    label: "Occupancy",
    value: "72%",
    detail: "54 of 75 rooms",
    icon: BedDouble,
  },
  {
    label: "Arrivals",
    value: "18",
    detail: "6 before noon",
    icon: CalendarCheck2,
  },
  {
    label: "Departures",
    value: "11",
    detail: "4 pending balance",
    icon: CreditCard,
  },
  {
    label: "Housekeeping",
    value: "12",
    detail: "dirty rooms",
    icon: Sparkles,
  },
];

const quickActions = [
  {
    to: "/rooms",
    label: "Rooms Board",
    icon: BedDouble,
    detail: "Availability and room status",
  },
  {
    to: "/reservations",
    label: "Reservations",
    icon: CalendarCheck2,
    detail: "Arrivals, stays and departures",
  },
  {
    to: "/housekeeping",
    label: "Housekeeping",
    icon: Sparkles,
    detail: "Cleaning queue and inspections",
  },
  {
    to: "/billing",
    label: "Billing",
    icon: CreditCard,
    detail: "Guest accounts and balances",
  },
];

const activityItems = [
  {
    time: "09:10",
    title: "Room 206 moved to inspection",
    detail: "Supervisor release needed before arrival.",
  },
  {
    time: "09:35",
    title: "Reservation CR-2048 checked in",
    detail: "Guest profile completed at reception.",
  },
  {
    time: "10:05",
    title: "Room 104 marked high priority",
    detail: "Checkout clean before 14:00.",
  },
  {
    time: "10:40",
    title: "Billing account pending payment",
    detail: "Room 312 has EUR 86.00 outstanding.",
  },
];

const attentionItems = [
  "4 rooms blocked by maintenance",
  "5 high-priority cleaning tasks",
  "3 guest accounts with open balance",
];

export function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Today at a glance"
      />

      <section className="metric-grid">
        {dashboardMetrics.map((metric) => {
          const Icon = metric.icon;

          return (
            <article className="metric-card" key={metric.label}>
              <div className="metric-card-icon">
                <Icon size={20} aria-hidden="true" />
              </div>
              <div>
                <p className="metric-label">{metric.label}</p>
                <strong className="metric-value">{metric.value}</strong>
                <p className="metric-detail">{metric.detail}</p>
              </div>
            </article>
          );
        })}
      </section>

      <section className="dashboard-layout">
        <div className="content-panel">
          <div className="panel-heading">
            <div>
              <h2>Operational Flow</h2>
              <p>Main work areas for the current shift</p>
            </div>
          </div>

          <div className="quick-action-grid">
            {quickActions.map((action) => {
              const Icon = action.icon;

              return (
                <NavLink
                  className="quick-action"
                  key={action.to}
                  to={action.to}
                >
                  <Icon size={20} aria-hidden="true" />
                  <span>
                    <strong>{action.label}</strong>
                    <small>{action.detail}</small>
                  </span>
                </NavLink>
              );
            })}
          </div>
        </div>

        <aside className="content-panel side-panel">
          <div className="panel-heading">
            <div>
              <h2>Needs Attention</h2>
              <p>Open items for supervisors</p>
            </div>
            <AlertTriangle size={20} aria-hidden="true" />
          </div>

          <div className="attention-list">
            {attentionItems.map((item) => (
              <div className="attention-item" key={item}>
                <span />
                <p>{item}</p>
              </div>
            ))}
          </div>
        </aside>
      </section>

      <section className="dashboard-layout lower-dashboard">
        <div className="content-panel">
          <div className="panel-heading">
            <div>
              <h2>Activity</h2>
              <p>Latest operational updates</p>
            </div>
          </div>

          <div className="timeline-list">
            {activityItems.map((item) => (
              <article className="timeline-item" key={item.title}>
                <time>{item.time}</time>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.detail}</p>
                </div>
              </article>
            ))}
          </div>
        </div>

        <aside className="content-panel side-panel">
          <div className="panel-heading">
            <div>
              <h2>Guest Snapshot</h2>
              <p>Front desk load</p>
            </div>
            <Users size={20} aria-hidden="true" />
          </div>

          <div className="snapshot-list">
            <div>
              <span>In house</span>
              <strong>96</strong>
            </div>
            <div>
              <span>Adults</span>
              <strong>82</strong>
            </div>
            <div>
              <span>Children</span>
              <strong>14</strong>
            </div>
          </div>
        </aside>
      </section>
    </>
  );
}
