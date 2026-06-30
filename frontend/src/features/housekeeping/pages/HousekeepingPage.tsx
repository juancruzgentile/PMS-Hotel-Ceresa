import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  ClipboardList,
  SprayCan,
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

type CleaningStatusFilter = "all" | "dirty" | "in_progress" | "clean";

const cleaningStatuses = ["dirty", "in_progress", "clean"] as const;

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected API error.";
}

function statusClass(status: string) {
  return `status-pill status-${status.replace("_", "-")}`;
}

function isRoomReady(room: Room): boolean {
  return (
    room.room_status === "available" &&
    room.cleaning_status === "clean" &&
    room.maintenance_status === "ok"
  );
}

function getReadyLabel(room: Room): string {
  if (isRoomReady(room)) {
    return "Ready";
  }

  if (room.maintenance_status !== "ok") {
    return "Maintenance";
  }

  if (room.cleaning_status !== "clean") {
    return "Needs cleaning";
  }

  return "Not ready";
}

export function HousekeepingPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [dirtyRooms, setDirtyRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [cleaningFilter, setCleaningFilter] =
    useState<CleaningStatusFilter>("all");
  const [floorFilter, setFloorFilter] = useState("");
  const [roomTypeFilter, setRoomTypeFilter] = useState("");
  const [nextCleaningStatus, setNextCleaningStatus] = useState("clean");
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [lastOperation, setLastOperation] = useState<string | null>(null);

  async function loadHousekeepingData() {
    setIsLoading(true);
    setError(null);

    try {
      const [allRooms, roomsNeedingCleaning] = await Promise.all([
        apiRequest<Room[]>(endpoints.rooms.list),
        apiRequest<Room[]>(endpoints.housekeeping.dirtyRooms),
      ]);

      setRooms(allRooms);
      setDirtyRooms(roomsNeedingCleaning);
      setLastMessage(
        `${allRooms.length} room(s) loaded; ${roomsNeedingCleaning.length} dirty room(s).`,
      );

      if (selectedRoom) {
        const refreshedSelection = allRooms.find(
          (room) => room.id === selectedRoom.id,
        );
        setSelectedRoom(refreshedSelection ?? null);

        if (refreshedSelection) {
          setNextCleaningStatus(refreshedSelection.cleaning_status);
        }
      }
    } catch (loadError) {
      setError(`API error: ${getErrorMessage(loadError)}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadHousekeepingData();
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
      const matchesCleaning =
        cleaningFilter === "all" ||
        room.cleaning_status === cleaningFilter;
      const matchesFloor =
        floorFilter === "" || String(room.floor) === floorFilter;
      const matchesRoomType =
        roomTypeFilter === "" || room.room_type === roomTypeFilter;
      const matchesSearch =
        normalizedSearch === "" ||
        room.room_number.toLowerCase().includes(normalizedSearch);

      return (
        matchesCleaning &&
        matchesFloor &&
        matchesRoomType &&
        matchesSearch
      );
    });
  }, [rooms, searchTerm, cleaningFilter, floorFilter, roomTypeFilter]);

  const inProgressCount = rooms.filter(
    (room) => room.cleaning_status === "in_progress",
  ).length;
  const readyCount = rooms.filter(isRoomReady).length;
  const notReadyCount = rooms.length - readyCount;

  function selectRoom(room: Room) {
    setSelectedRoom(room);
    setNextCleaningStatus(room.cleaning_status);
    setLastOperation(`Room ${room.room_number} selected.`);
  }

  async function updateCleaningStatus() {
    if (!selectedRoom) {
      setError("Select a room before updating cleaning status.");
      return;
    }

    setIsUpdating(true);
    setError(null);

    try {
      await apiRequest(endpoints.rooms.status(selectedRoom.id), {
        method: "PATCH",
        body: {
          cleaning_status: nextCleaningStatus,
        },
      });

      setLastOperation(
        `Room ${selectedRoom.room_number} cleaning status updated to ${nextCleaningStatus}.`,
      );
      await loadHousekeepingData();
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
        title="Housekeeping"
        description="Operational cleaning board for room readiness."
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
            <p className="metric-label">Dirty rooms</p>
            <strong className="metric-value">{dirtyRooms.length}</strong>
            <p className="metric-detail">From Housekeeping endpoint</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <SprayCan size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">In progress</p>
            <strong className="metric-value">{inProgressCount}</strong>
            <p className="metric-detail">Cleaning underway</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <CheckCircle2 size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Ready rooms</p>
            <strong className="metric-value">{readyCount}</strong>
            <p className="metric-detail">Available, clean and OK</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <ClipboardList size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Not ready</p>
            <strong className="metric-value">{notReadyCount}</strong>
            <p className="metric-detail">Cleaning, occupied or repair</p>
          </div>
        </article>
      </section>

      <section className="housekeeping-layout">
        <div className="content-panel">
          <div className="panel-heading">
            <div>
              <h2>Room queue</h2>
              <p>Filter rooms locally using the current Rooms API.</p>
            </div>
            <button
              className="secondary-button"
              disabled={busy}
              onClick={() => void loadHousekeepingData()}
            >
              Refresh
            </button>
          </div>

          <div className="rooms-toolbar housekeeping-toolbar">
            <label>
              Room search
              <input
                placeholder="Room number"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </label>
            <label>
              Cleaning
              <select
                value={cleaningFilter}
                onChange={(event) =>
                  setCleaningFilter(
                    event.target.value as CleaningStatusFilter,
                  )
                }
              >
                <option value="all">All</option>
                {cleaningStatuses.map((status) => (
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
            <p className="muted-text">Loading housekeeping rooms...</p>
          ) : rooms.length === 0 ? (
            <EmptyState
              title="No rooms yet"
              message="Create rooms first, then return to Housekeeping."
            />
          ) : filteredRooms.length === 0 ? (
            <EmptyState
              title="No matching rooms"
              message="Adjust the filters or refresh the room list."
            />
          ) : (
            <div className="housekeeping-table">
              <div className="housekeeping-table-row housekeeping-table-head">
                <span>ID</span>
                <span>Room</span>
                <span>Floor</span>
                <span>Type</span>
                <span>Room status</span>
                <span>Cleaning</span>
                <span>Maintenance</span>
                <span>Readiness</span>
                <span>Notes</span>
              </div>
              {filteredRooms.map((room) => (
                <button
                  className={`housekeeping-table-row ${
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
                  <span>
                    <span className={statusClass(room.cleaning_status)}>
                      {room.cleaning_status}
                    </span>
                  </span>
                  <span>{room.maintenance_status}</span>
                  <span>{getReadyLabel(room)}</span>
                  <span>{room.notes ?? "-"}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <aside className="housekeeping-detail">
          <section className="content-panel mvp-summary">
            <h2>Room detail</h2>
            {selectedRoom ? (
              <>
                {isRoomReady(selectedRoom) ? (
                  <div className="success-banner">
                    Room appears ready for operation.
                  </div>
                ) : (
                  <div className="warning-banner">
                    Room is not ready. Review cleaning, occupancy or
                    maintenance status.
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
                Select a room to inspect housekeeping readiness.
              </p>
            )}
          </section>

          <section className="content-panel mvp-summary">
            <h2>Cleaning status</h2>
            <p>
              Updates use the existing room status endpoint and only change
              cleaning_status.
            </p>
            <div className="form-grid single-column">
              <label>
                Next status
                <select
                  value={nextCleaningStatus}
                  onChange={(event) =>
                    setNextCleaningStatus(event.target.value)
                  }
                >
                  {cleaningStatuses.map((status) => (
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
                selectedRoom.cleaning_status === nextCleaningStatus
              }
              onClick={() => void updateCleaningStatus()}
            >
              Update cleaning status
            </button>
          </section>

          <section className="content-panel mvp-summary">
            <div className="panel-heading compact">
              <div>
                <h2>Dirty queue</h2>
                <p>Rooms returned by `/housekeeping/dirty-rooms`.</p>
              </div>
              <Clock3 size={18} aria-hidden="true" />
            </div>
            {dirtyRooms.length === 0 ? (
              <p className="muted-text">No dirty rooms reported.</p>
            ) : (
              <ol className="audit-list">
                {dirtyRooms.map((room) => (
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
