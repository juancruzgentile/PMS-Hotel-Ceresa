import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  ClipboardList,
  PackageCheck,
  SprayCan,
  UserCheck,
} from "lucide-react";

import { PageHeader } from "@/shared/components/PageHeader";

type HousekeepingTask = {
  room: string;
  floor: string;
  status: "Dirty" | "In progress" | "Inspection" | "Clean";
  priority: "High" | "Normal";
  assignedTo: string;
  nextStep: string;
  roomType: string;
  eta: string;
};

const summaryItems = [
  {
    label: "Dirty rooms",
    value: "12",
    detail: "5 high priority",
    icon: AlertTriangle,
  },
  {
    label: "In progress",
    value: "7",
    detail: "3 attendants active",
    icon: SprayCan,
  },
  {
    label: "Waiting inspection",
    value: "4",
    detail: "Supervisor queue",
    icon: ClipboardList,
  },
  {
    label: "Ready today",
    value: "28",
    detail: "Clean and released",
    icon: CheckCircle2,
  },
];

const tasks: HousekeepingTask[] = [
  {
    room: "104",
    floor: "Floor 1",
    status: "Dirty",
    priority: "High",
    assignedTo: "Marta Ruiz",
    nextStep: "Checkout clean before 14:00",
    roomType: "Double",
    eta: "35 min",
  },
  {
    room: "118",
    floor: "Floor 1",
    status: "In progress",
    priority: "Normal",
    assignedTo: "Sofia Conti",
    nextStep: "Replace towels and minibar report",
    roomType: "Suite",
    eta: "20 min",
  },
  {
    room: "206",
    floor: "Floor 2",
    status: "Inspection",
    priority: "High",
    assignedTo: "Lucas Meyer",
    nextStep: "Supervisor release for arrival",
    roomType: "Family",
    eta: "10 min",
  },
  {
    room: "312",
    floor: "Floor 3",
    status: "Dirty",
    priority: "Normal",
    assignedTo: "Unassigned",
    nextStep: "Assign attendant",
    roomType: "Single",
    eta: "Unplanned",
  },
  {
    room: "417",
    floor: "Floor 4",
    status: "Clean",
    priority: "Normal",
    assignedTo: "Nadia Silva",
    nextStep: "Room ready",
    roomType: "Double",
    eta: "Done",
  },
];

const attendantLoad = [
  { name: "Marta Ruiz", rooms: 6, shift: "Morning", done: 3 },
  { name: "Sofia Conti", rooms: 5, shift: "Morning", done: 2 },
  { name: "Lucas Meyer", rooms: 4, shift: "Afternoon", done: 1 },
  { name: "Nadia Silva", rooms: 5, shift: "Afternoon", done: 4 },
];

const inspectionQueue = [
  { room: "206", note: "Arrival at 15:20" },
  { room: "305", note: "VIP amenities placed" },
  { room: "408", note: "Maintenance follow-up" },
];

const supplies = [
  { label: "Towels", value: "82%" },
  { label: "Linen", value: "68%" },
  { label: "Amenities", value: "74%" },
];

function statusClass(status: HousekeepingTask["status"]) {
  return `status-pill status-${status.toLowerCase().replace(" ", "-")}`;
}

export function HousekeepingPage() {
  return (
    <>
      <PageHeader
        title="Housekeeping"
        description="Cleaning board"
      />

      <section className="toolbar-panel" aria-label="Housekeeping filters">
        <button className="toolbar-button active" type="button">
          All rooms
        </button>
        <button className="toolbar-button" type="button">
          Dirty
        </button>
        <button className="toolbar-button" type="button">
          In progress
        </button>
        <button className="toolbar-button" type="button">
          Inspection
        </button>
        <button className="toolbar-button" type="button">
          Clean
        </button>
      </section>

      <section className="metric-grid">
        {summaryItems.map((item) => {
          const Icon = item.icon;

          return (
            <article className="metric-card" key={item.label}>
              <div className="metric-card-icon">
                <Icon size={20} aria-hidden="true" />
              </div>
              <div>
                <p className="metric-label">{item.label}</p>
                <strong className="metric-value">{item.value}</strong>
                <p className="metric-detail">{item.detail}</p>
              </div>
            </article>
          );
        })}
      </section>

      <section className="housekeeping-layout">
        <div className="content-panel">
          <div className="panel-heading">
            <div>
              <h2>Room Queue</h2>
              <p>Current cleaning plan</p>
            </div>
            <span className="panel-time">
              <Clock3 size={16} aria-hidden="true" />
              11:30
            </span>
          </div>

          <div className="data-table">
            <div className="data-table-row data-table-head">
              <span>Room</span>
              <span>Type</span>
              <span>Status</span>
              <span>Priority</span>
              <span>Assigned</span>
              <span>ETA</span>
              <span>Next step</span>
            </div>
            {tasks.map((task) => (
              <div className="data-table-row" key={task.room}>
                <span>
                  <strong>{task.room}</strong>
                  <small>{task.floor}</small>
                </span>
                <span>{task.roomType}</span>
                <span>
                  <span className={statusClass(task.status)}>
                    {task.status}
                  </span>
                </span>
                <span>{task.priority}</span>
                <span>{task.assignedTo}</span>
                <span>{task.eta}</span>
                <span>{task.nextStep}</span>
              </div>
            ))}
          </div>
        </div>

        <aside className="content-panel side-panel">
          <div className="panel-heading">
            <div>
              <h2>Attendants</h2>
              <p>Assigned rooms</p>
            </div>
            <UserCheck size={20} aria-hidden="true" />
          </div>

          <div className="attendant-list">
            {attendantLoad.map((attendant) => (
              <div className="attendant-item" key={attendant.name}>
                <div>
                  <strong>{attendant.name}</strong>
                  <span>{attendant.shift}</span>
                </div>
                <strong>
                  {attendant.done}/{attendant.rooms}
                </strong>
              </div>
            ))}
          </div>
        </aside>
      </section>

      <section className="housekeeping-layout lower-dashboard">
        <div className="content-panel">
          <div className="panel-heading">
            <div>
              <h2>Inspection Queue</h2>
              <p>Rooms waiting for supervisor release</p>
            </div>
            <ClipboardList size={20} aria-hidden="true" />
          </div>

          <div className="inspection-grid">
            {inspectionQueue.map((item) => (
              <article className="inspection-card" key={item.room}>
                <strong>Room {item.room}</strong>
                <p>{item.note}</p>
              </article>
            ))}
          </div>
        </div>

        <aside className="content-panel side-panel">
          <div className="panel-heading">
            <div>
              <h2>Supplies</h2>
              <p>Floor stock</p>
            </div>
            <PackageCheck size={20} aria-hidden="true" />
          </div>

          <div className="snapshot-list">
            {supplies.map((item) => (
              <div key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </aside>
      </section>
    </>
  );
}
