import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

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

function getBooleanLabel(value: boolean | number): string {
  return value === true || value === 1 ? "Yes" : "No";
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected API error.";
}

export function RoomsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [roomStatusFilter, setRoomStatusFilter] = useState("");
  const [cleaningStatusFilter, setCleaningStatusFilter] = useState("");
  const [maintenanceStatusFilter, setMaintenanceStatusFilter] =
    useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  async function loadRooms() {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiRequest<Room[]>(endpoints.rooms.list);

      setRooms(data);
      setLastMessage(`${data.length} room(s) loaded.`);

      if (selectedRoom) {
        const refreshedSelection = data.find(
          (room) => room.id === selectedRoom.id,
        );
        setSelectedRoom(refreshedSelection ?? null);
      }
    } catch (loadError) {
      setError(`API error: ${getErrorMessage(loadError)}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadRooms();
    // Initial page load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const roomStatusOptions = useMemo(
    () =>
      Array.from(new Set(rooms.map((room) => room.room_status))).sort(),
    [rooms],
  );
  const cleaningStatusOptions = useMemo(
    () =>
      Array.from(
        new Set(rooms.map((room) => room.cleaning_status)),
      ).sort(),
    [rooms],
  );
  const maintenanceStatusOptions = useMemo(
    () =>
      Array.from(
        new Set(rooms.map((room) => room.maintenance_status)),
      ).sort(),
    [rooms],
  );

  const filteredRooms = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return rooms.filter((room) => {
      const matchesRoomStatus =
        roomStatusFilter === "" ||
        room.room_status === roomStatusFilter;
      const matchesCleaningStatus =
        cleaningStatusFilter === "" ||
        room.cleaning_status === cleaningStatusFilter;
      const matchesMaintenanceStatus =
        maintenanceStatusFilter === "" ||
        room.maintenance_status === maintenanceStatusFilter;
      const matchesSearch =
        normalizedSearch === "" ||
        room.room_number.toLowerCase().includes(normalizedSearch) ||
        room.room_type.toLowerCase().includes(normalizedSearch) ||
        room.room_status.toLowerCase().includes(normalizedSearch) ||
        room.cleaning_status.toLowerCase().includes(normalizedSearch) ||
        room.maintenance_status.toLowerCase().includes(normalizedSearch) ||
        String(room.floor).includes(normalizedSearch);

      return (
        matchesRoomStatus &&
        matchesCleaningStatus &&
        matchesMaintenanceStatus &&
        matchesSearch
      );
    });
  }, [
    rooms,
    searchTerm,
    roomStatusFilter,
    cleaningStatusFilter,
    maintenanceStatusFilter,
  ]);

  async function selectRoom(room: Room) {
    setIsDetailLoading(true);
    setError(null);

    try {
      const detail = await apiRequest<Room>(
        endpoints.rooms.detail(room.id),
      );

      setSelectedRoom(detail);
      setLastMessage(`Room ${detail.room_number} selected.`);
    } catch (detailError) {
      setError(`API error: ${getErrorMessage(detailError)}`);
    } finally {
      setIsDetailLoading(false);
    }
  }

  async function copyRoomId() {
    if (!selectedRoom) {
      return;
    }

    try {
      await navigator.clipboard.writeText(String(selectedRoom.id));
      setLastMessage(`room_id ${selectedRoom.id} copied.`);
    } catch {
      setLastMessage(
        `room_id ${selectedRoom.id} is ready to copy manually.`,
      );
    }
  }

  return (
    <>
      <PageHeader
        title="Rooms"
        description="List, search and inspect room operational status."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {lastMessage ? (
        <div className="success-banner">{lastMessage}</div>
      ) : null}

      <section className="rooms-layout">
        <div className="rooms-main">
          <section className="content-panel">
            <div className="panel-heading">
              <div>
                <h2>Room list</h2>
                <p>
                  Search locally by number, type, status or floor.
                </p>
              </div>
              <button
                className="secondary-button"
                disabled={isLoading}
                onClick={() => void loadRooms()}
              >
                Refresh
              </button>
            </div>

            <div className="rooms-toolbar">
              <label>
                Search
                <input
                  placeholder="Number, type, status or floor"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                />
              </label>
              <label>
                Room status
                <select
                  value={roomStatusFilter}
                  onChange={(event) =>
                    setRoomStatusFilter(event.target.value)
                  }
                >
                  <option value="">All</option>
                  {roomStatusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Cleaning
                <select
                  value={cleaningStatusFilter}
                  onChange={(event) =>
                    setCleaningStatusFilter(event.target.value)
                  }
                >
                  <option value="">All</option>
                  {cleaningStatusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Maintenance
                <select
                  value={maintenanceStatusFilter}
                  onChange={(event) =>
                    setMaintenanceStatusFilter(event.target.value)
                  }
                >
                  <option value="">All</option>
                  {maintenanceStatusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {isLoading ? (
              <p className="muted-text">Loading rooms...</p>
            ) : rooms.length === 0 ? (
              <EmptyState
                title="No rooms yet"
                message="Create a room from Reception MVP or another workflow, then refresh this list."
              />
            ) : filteredRooms.length === 0 ? (
              <EmptyState
                title="No matches"
                message="Adjust the search text or status filters."
              />
            ) : (
              <div className="rooms-table">
                <div className="rooms-table-row rooms-table-head">
                  <span>ID</span>
                  <span>Room</span>
                  <span>Floor</span>
                  <span>Type</span>
                  <span>Room status</span>
                  <span>Cleaning</span>
                  <span>Maintenance</span>
                  <span>Balcony</span>
                  <span>Jacuzzi</span>
                  <span>Notes</span>
                </div>
                {filteredRooms.map((room) => (
                  <button
                    className={`rooms-table-row ${
                      selectedRoom?.id === room.id ? "selected" : ""
                    }`}
                    key={room.id}
                    onClick={() => void selectRoom(room)}
                  >
                    <span>{room.id}</span>
                    <span>{room.room_number}</span>
                    <span>{room.floor}</span>
                    <span>{room.room_type}</span>
                    <span>{room.room_status}</span>
                    <span>{room.cleaning_status}</span>
                    <span>{room.maintenance_status}</span>
                    <span>{getBooleanLabel(room.has_balcony)}</span>
                    <span>{getBooleanLabel(room.has_jacuzzi)}</span>
                    <span>{room.notes ?? "-"}</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>

        <aside className="rooms-detail">
          <section className="content-panel mvp-summary">
            <h2>Room detail</h2>
            {isDetailLoading ? (
              <p className="muted-text">Loading detail...</p>
            ) : selectedRoom ? (
              <>
                <dl>
                  <div>
                    <dt>ID</dt>
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
                  <div>
                    <dt>Balcony</dt>
                    <dd>{getBooleanLabel(selectedRoom.has_balcony)}</dd>
                  </div>
                  <div>
                    <dt>Jacuzzi</dt>
                    <dd>{getBooleanLabel(selectedRoom.has_jacuzzi)}</dd>
                  </div>
                </dl>

                {selectedRoom.notes ? (
                  <p className="detail-note">{selectedRoom.notes}</p>
                ) : null}

                <div className="detail-actions">
                  <button
                    className="secondary-button"
                    onClick={() => void copyRoomId()}
                  >
                    Copy room ID
                  </button>
                  <Link className="text-link" to="/reservations">
                    Open Reservations
                  </Link>
                </div>
              </>
            ) : (
              <p className="muted-text">
                Select a room to inspect operational details.
              </p>
            )}
          </section>

          <section className="content-panel mvp-summary">
            <h2>Reservation helper</h2>
            {selectedRoom ? (
              <p>
                Use room_id <strong>{selectedRoom.id}</strong> when
                creating reservations or testing Reception MVP.
              </p>
            ) : (
              <p className="muted-text">
                Select a room to see the ID needed for reservations.
              </p>
            )}
          </section>
        </aside>
      </section>
    </>
  );
}
