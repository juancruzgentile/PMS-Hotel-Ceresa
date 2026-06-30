import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  ShieldAlert,
  Wrench,
} from "lucide-react";

import { apiRequest } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { EmptyState } from "@/shared/components/EmptyState";
import { PageHeader } from "@/shared/components/PageHeader";

type Room = {
  id: number;
  room_number: string;
  floor: number;
  room_type: string;
  room_status: string;
  cleaning_status: string;
  maintenance_status: string;
  has_balcony: boolean | number;
  has_jacuzzi: boolean | number;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

type MaintenanceStatusFilter =
  | "all"
  | "needs_repair"
  | "in_repair"
  | "ok";

const maintenanceStatuses = ["needs_repair", "in_repair", "ok"] as const;

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected API error.";
}

function maintenanceStatusClass(status: string) {
  if (status === "ok") {
    return "status-pill status-clean";
  }

  if (status === "in_repair") {
    return "status-pill status-in-progress";
  }

  return "status-pill status-dirty";
}

function isRoomOperational(room: Room): boolean {
  return (
    room.room_status !== "out_of_service" &&
    room.maintenance_status === "ok"
  );
}

function getOperationalLabel(room: Room): string {
  if (isRoomOperational(room)) {
    return "Operational";
  }

  if (room.maintenance_status === "in_repair") {
    return "In repair";
  }

  if (room.maintenance_status === "needs_repair") {
    return "Blocked by repair";
  }

  return "Out of service";
}

export function MaintenancePage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [repairRooms, setRepairRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [maintenanceFilter, setMaintenanceFilter] =
    useState<MaintenanceStatusFilter>("all");
  const [floorFilter, setFloorFilter] = useState("");
  const [roomTypeFilter, setRoomTypeFilter] = useState("");
  const [nextMaintenanceStatus, setNextMaintenanceStatus] =
    useState("needs_repair");
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [lastOperation, setLastOperation] = useState<string | null>(null);

  async function loadMaintenanceData() {
    setIsLoading(true);
    setError(null);

    try {
      const [allRooms, roomsNeedingRepair] = await Promise.all([
        apiRequest<Room[]>(endpoints.rooms.list),
        apiRequest<Room[]>(endpoints.maintenance.repairRooms),
      ]);

      setRooms(allRooms);
      setRepairRooms(roomsNeedingRepair);
      setLastMessage(
        `${allRooms.length} room(s) loaded; ${roomsNeedingRepair.length} repair room(s).`,
      );

      if (selectedRoom) {
        const refreshedSelection = allRooms.find(
          (room) => room.id === selectedRoom.id,
        );
        setSelectedRoom(refreshedSelection ?? null);

        if (refreshedSelection) {
          setNextMaintenanceStatus(
            refreshedSelection.maintenance_status,
          );
        }
      }
    } catch (loadError) {
      setError(`API error: ${getErrorMessage(loadError)}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadMaintenanceData();
    // Initial page load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const floorOptions = useMemo(
    () =>
      Array.from(new Set(rooms.map((room) => String(room.floor)))).sort(
        (left, right) => Number(left) - Number(right),
      ),
    [rooms],
  );

  const roomTypeOptions = useMemo(
    () => Array.from(new Set(rooms.map((room) => room.room_type))).sort(),
    [rooms],
  );

  const filteredRooms = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return rooms.filter((room) => {
      const matchesMaintenance =
        maintenanceFilter === "all" ||
        room.maintenance_status === maintenanceFilter;
      const matchesFloor =
        floorFilter === "" || String(room.floor) === floorFilter;
      const matchesRoomType =
        roomTypeFilter === "" || room.room_type === roomTypeFilter;
      const matchesSearch =
        normalizedSearch === "" ||
        room.room_number.toLowerCase().includes(normalizedSearch) ||
        (room.notes ?? "").toLowerCase().includes(normalizedSearch);

      return (
        matchesMaintenance &&
        matchesFloor &&
        matchesRoomType &&
        matchesSearch
      );
    });
  }, [rooms, searchTerm, maintenanceFilter, floorFilter, roomTypeFilter]);

  const inRepairCount = rooms.filter(
    (room) => room.maintenance_status === "in_repair",
  ).length;
  const operationalCount = rooms.filter(isRoomOperational).length;
  const blockedCount = rooms.length - operationalCount;

  function selectRoom(room: Room) {
    setSelectedRoom(room);
    setNextMaintenanceStatus(room.maintenance_status);
    setLastOperation(`Room ${room.room_number} selected.`);
  }

  async function updateMaintenanceStatus() {
    if (!selectedRoom) {
      setError("Select a room before updating maintenance status.");
      return;
    }

    setIsUpdating(true);
    setError(null);

    try {
      await apiRequest(endpoints.rooms.status(selectedRoom.id), {
        method: "PATCH",
        body: {
          maintenance_status: nextMaintenanceStatus,
        },
      });

      setLastOperation(
        `Room ${selectedRoom.room_number} maintenance status updated to ${nextMaintenanceStatus}.`,
      );
      await loadMaintenanceData();
    } catch (updateError) {
      setError(`API error: ${getErrorMessage(updateError)}`);
    } finally {
      setIsUpdating(false);
    }
  }

  const busy = isLoading || isUpdating;

  return (
    <>
      <PageHeader
        title="Maintenance"
        description="Operational room maintenance board using current room statuses."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {lastMessage ? (
        <div className="success-banner">{lastMessage}</div>
      ) : null}
      {lastOperation ? (
        <div className="success-banner">{lastOperation}</div>
      ) : null}

      <section className="metric-grid">
        <article className="metric-card">
          <div className="metric-card-icon">
            <AlertTriangle size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Needs repair</p>
            <strong className="metric-value">{repairRooms.length}</strong>
            <p className="metric-detail">From Maintenance endpoint</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <Wrench size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">In repair</p>
            <strong className="metric-value">{inRepairCount}</strong>
            <p className="metric-detail">Work currently active</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <CheckCircle2 size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Operational</p>
            <strong className="metric-value">{operationalCount}</strong>
            <p className="metric-detail">Not out of service and OK</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <ShieldAlert size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Blocked</p>
            <strong className="metric-value">{blockedCount}</strong>
            <p className="metric-detail">Repair or out of service</p>
          </div>
        </article>
      </section>

      <section className="maintenance-layout">
        <div className="content-panel">
          <div className="panel-heading">
            <div>
              <h2>Room maintenance queue</h2>
              <p>
                Filter rooms locally. This is not a full ticket system yet.
              </p>
            </div>
            <button
              className="secondary-button"
              disabled={busy}
              onClick={() => void loadMaintenanceData()}
            >
              Refresh
            </button>
          </div>

          <div className="rooms-toolbar maintenance-toolbar">
            <label>
              Search
              <input
                placeholder="Room number or notes"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </label>
            <label>
              Maintenance
              <select
                value={maintenanceFilter}
                onChange={(event) =>
                  setMaintenanceFilter(
                    event.target.value as MaintenanceStatusFilter,
                  )
                }
              >
                <option value="all">All</option>
                {maintenanceStatuses.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Floor
              <select
                value={floorFilter}
                onChange={(event) => setFloorFilter(event.target.value)}
              >
                <option value="">All floors</option>
                {floorOptions.map((floor) => (
                  <option key={floor} value={floor}>
                    Floor {floor}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Room type
              <select
                value={roomTypeFilter}
                onChange={(event) => setRoomTypeFilter(event.target.value)}
              >
                <option value="">All types</option>
                {roomTypeOptions.map((roomType) => (
                  <option key={roomType} value={roomType}>
                    {roomType}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {isLoading ? (
            <p className="muted-text">Loading maintenance rooms...</p>
          ) : rooms.length === 0 ? (
            <EmptyState
              title="No rooms yet"
              message="Create rooms first, then return to Maintenance."
            />
          ) : filteredRooms.length === 0 ? (
            <EmptyState
              title="No matching rooms"
              message="Adjust the filters or refresh the room list."
            />
          ) : (
            <div className="maintenance-table">
              <div className="maintenance-table-row maintenance-table-head">
                <span>ID</span>
                <span>Room</span>
                <span>Floor</span>
                <span>Type</span>
                <span>Room status</span>
                <span>Cleaning</span>
                <span>Maintenance</span>
                <span>Operation</span>
                <span>Notes</span>
              </div>
              {filteredRooms.map((room) => (
                <button
                  className={`maintenance-table-row ${
                    selectedRoom?.id === room.id ? "selected" : ""
                  }`}
                  key={room.id}
                  onClick={() => selectRoom(room)}
                >
                  <span>{room.id}</span>
                  <span>
                    <strong>{room.room_number}</strong>
                  </span>
                  <span>{room.floor}</span>
                  <span>{room.room_type}</span>
                  <span>{room.room_status}</span>
                  <span>{room.cleaning_status}</span>
                  <span>
                    <span
                      className={maintenanceStatusClass(
                        room.maintenance_status,
                      )}
                    >
                      {room.maintenance_status}
                    </span>
                  </span>
                  <span>{getOperationalLabel(room)}</span>
                  <span>{room.notes ?? "-"}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <aside className="maintenance-detail">
          <section className="content-panel mvp-summary">
            <h2>Room detail</h2>
            {selectedRoom ? (
              <>
                {isRoomOperational(selectedRoom) ? (
                  <div className="success-banner">
                    Room appears operational from maintenance status.
                  </div>
                ) : (
                  <div className="warning-banner">
                    Room appears blocked or under repair. Review room and
                    maintenance status before using it.
                  </div>
                )}

                <dl>
                  <div>
                    <dt>room_id</dt>
                    <dd>{selectedRoom.id}</dd>
                  </div>
                  <div>
                    <dt>Room</dt>
                    <dd>{selectedRoom.room_number}</dd>
                  </div>
                  <div>
                    <dt>Floor</dt>
                    <dd>{selectedRoom.floor}</dd>
                  </div>
                  <div>
                    <dt>Type</dt>
                    <dd>{selectedRoom.room_type}</dd>
                  </div>
                  <div>
                    <dt>Room status</dt>
                    <dd>{selectedRoom.room_status}</dd>
                  </div>
                  <div>
                    <dt>Cleaning</dt>
                    <dd>{selectedRoom.cleaning_status}</dd>
                  </div>
                  <div>
                    <dt>Maintenance</dt>
                    <dd>{selectedRoom.maintenance_status}</dd>
                  </div>
                </dl>

                {selectedRoom.notes ? (
                  <p className="detail-note">{selectedRoom.notes}</p>
                ) : null}

                <div className="detail-actions">
                  <Link className="text-link" to="/rooms">
                    Open Rooms
                  </Link>
                </div>
              </>
            ) : (
              <p className="muted-text">
                Select a room to inspect maintenance status and operation.
              </p>
            )}
          </section>

          <section className="content-panel mvp-summary">
            <h2>Maintenance status</h2>
            <p>
              This updates the existing room status record only. It does
              not create a full maintenance ticket.
            </p>
            <div className="form-grid single-column">
              <label>
                Next status
                <select
                  value={nextMaintenanceStatus}
                  onChange={(event) =>
                    setNextMaintenanceStatus(event.target.value)
                  }
                >
                  {maintenanceStatuses.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button
              className="primary-button full-width-button"
              disabled={
                busy ||
                !selectedRoom ||
                selectedRoom.maintenance_status === nextMaintenanceStatus
              }
              onClick={() => void updateMaintenanceStatus()}
            >
              Update maintenance status
            </button>
          </section>

          <section className="content-panel mvp-summary">
            <div className="panel-heading compact">
              <div>
                <h2>Repair queue</h2>
                <p>Rooms returned by `/maintenance/repair-rooms`.</p>
              </div>
              <Clock3 size={18} aria-hidden="true" />
            </div>
            {repairRooms.length === 0 ? (
              <p className="muted-text">No rooms need repair right now.</p>
            ) : (
              <ol className="audit-list">
                {repairRooms.map((room) => (
                  <li key={room.id}>
                    <strong>Room {room.room_number}</strong>
                    <span>
                      Floor {room.floor} - {room.room_type}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </aside>
      </section>
    </>
  );
}
