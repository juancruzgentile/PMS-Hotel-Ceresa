import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { apiRequest } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { EmptyState } from "@/shared/components/EmptyState";
import { PageHeader } from "@/shared/components/PageHeader";

type Guest = {
  id: number;
  guest_code: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  nationality: string | null;
  notes: string | null;
  is_active: boolean | number;
  created_at: string;
  updated_at: string;
};

type GuestStatusFilter = "all" | "active" | "inactive";

function getGuestFullName(guest: Guest): string {
  return `${guest.first_name} ${guest.last_name}`;
}

function isGuestActive(guest: Guest): boolean {
  return guest.is_active === true || guest.is_active === 1;
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected API error.";
}

export function GuestsPage() {
  const [guests, setGuests] = useState<Guest[]>([]);
  const [selectedGuest, setSelectedGuest] = useState<Guest | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<GuestStatusFilter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  async function loadGuests() {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiRequest<Guest[]>(endpoints.guests.list);

      setGuests(data);
      setLastMessage(`${data.length} guest(s) loaded.`);

      if (selectedGuest) {
        const refreshedSelection = data.find(
          (guest) => guest.id === selectedGuest.id,
        );
        setSelectedGuest(refreshedSelection ?? null);
      }
    } catch (loadError) {
      setError(`API error: ${getErrorMessage(loadError)}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadGuests();
    // Initial page load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredGuests = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return guests.filter((guest) => {
      const active = isGuestActive(guest);
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && active) ||
        (statusFilter === "inactive" && !active);
      const matchesSearch =
        normalizedSearch === "" ||
        guest.guest_code.toLowerCase().includes(normalizedSearch) ||
        guest.first_name.toLowerCase().includes(normalizedSearch) ||
        guest.last_name.toLowerCase().includes(normalizedSearch) ||
        (guest.email ?? "").toLowerCase().includes(normalizedSearch) ||
        (guest.phone ?? "").toLowerCase().includes(normalizedSearch);

      return matchesStatus && matchesSearch;
    });
  }, [guests, searchTerm, statusFilter]);

  async function selectGuest(guest: Guest) {
    setIsDetailLoading(true);
    setError(null);

    try {
      const detail = await apiRequest<Guest>(
        endpoints.guests.detail(guest.id),
      );

      setSelectedGuest(detail);
      setLastMessage(`Guest ${detail.guest_code} selected.`);
    } catch (detailError) {
      setError(`API error: ${getErrorMessage(detailError)}`);
    } finally {
      setIsDetailLoading(false);
    }
  }

  async function copyGuestId() {
    if (!selectedGuest) {
      return;
    }

    try {
      await navigator.clipboard.writeText(String(selectedGuest.id));
      setLastMessage(`guest_id ${selectedGuest.id} copied.`);
    } catch {
      setLastMessage(
        `guest_id ${selectedGuest.id} is ready to copy manually.`,
      );
    }
  }

  return (
    <>
      <PageHeader
        title="Guests"
        description="List, search and inspect guest profiles."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {lastMessage ? (
        <div className="success-banner">{lastMessage}</div>
      ) : null}

      <section className="guests-layout">
        <div className="guests-main">
          <section className="content-panel">
            <div className="panel-heading">
              <div>
                <h2>Guest list</h2>
                <p>Search locally by code, name, email or phone.</p>
              </div>
              <button
                className="secondary-button"
                disabled={isLoading}
                onClick={() => void loadGuests()}
              >
                Refresh
              </button>
            </div>

            <div className="guests-toolbar">
              <label>
                Search
                <input
                  placeholder="Code, name, email or phone"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                />
              </label>
              <label>
                Status
                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(
                      event.target.value as GuestStatusFilter,
                    )
                  }
                >
                  <option value="all">All guests</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </label>
            </div>

            {isLoading ? (
              <p className="muted-text">Loading guests...</p>
            ) : guests.length === 0 ? (
              <EmptyState
                title="No guests yet"
                message="Create a guest from Reception MVP or another workflow, then refresh this list."
              />
            ) : filteredGuests.length === 0 ? (
              <EmptyState
                title="No matches"
                message="Adjust the search text or status filter."
              />
            ) : (
              <div className="guests-table">
                <div className="guests-table-row guests-table-head">
                  <span>ID</span>
                  <span>Code</span>
                  <span>First name</span>
                  <span>Last name</span>
                  <span>Email</span>
                  <span>Phone</span>
                  <span>Nationality</span>
                  <span>Active</span>
                  <span>Created</span>
                </div>
                {filteredGuests.map((guest) => (
                  <button
                    className={`guests-table-row ${
                      selectedGuest?.id === guest.id ? "selected" : ""
                    }`}
                    key={guest.id}
                    onClick={() => void selectGuest(guest)}
                  >
                    <span>{guest.id}</span>
                    <span>{guest.guest_code}</span>
                    <span>{guest.first_name}</span>
                    <span>{guest.last_name}</span>
                    <span>{guest.email ?? "-"}</span>
                    <span>{guest.phone ?? "-"}</span>
                    <span>{guest.nationality ?? "-"}</span>
                    <span>{isGuestActive(guest) ? "Yes" : "No"}</span>
                    <span>{guest.created_at}</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>

        <aside className="guests-detail">
          <section className="content-panel mvp-summary">
            <h2>Guest detail</h2>
            {isDetailLoading ? (
              <p className="muted-text">Loading detail...</p>
            ) : selectedGuest ? (
              <>
                <dl>
                  <div>
                    <dt>ID</dt>
                    <dd>{selectedGuest.id}</dd>
                  </div>
                  <div>
                    <dt>Code</dt>
                    <dd>{selectedGuest.guest_code}</dd>
                  </div>
                  <div>
                    <dt>Name</dt>
                    <dd>{getGuestFullName(selectedGuest)}</dd>
                  </div>
                  <div>
                    <dt>Email</dt>
                    <dd>{selectedGuest.email ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>Phone</dt>
                    <dd>{selectedGuest.phone ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>Nationality</dt>
                    <dd>{selectedGuest.nationality ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>Active</dt>
                    <dd>{isGuestActive(selectedGuest) ? "Yes" : "No"}</dd>
                  </div>
                  <div>
                    <dt>Created</dt>
                    <dd>{selectedGuest.created_at}</dd>
                  </div>
                </dl>

                {selectedGuest.notes ? (
                  <p className="detail-note">{selectedGuest.notes}</p>
                ) : null}

                <div className="detail-actions">
                  <button
                    className="secondary-button"
                    onClick={() => void copyGuestId()}
                  >
                    Copy guest ID
                  </button>
                  <Link className="text-link" to="/reservations">
                    Open Reservations
                  </Link>
                </div>
              </>
            ) : (
              <p className="muted-text">
                Select a guest to inspect profile details.
              </p>
            )}
          </section>

          <section className="content-panel mvp-summary">
            <h2>Reservation helper</h2>
            {selectedGuest ? (
              <p>
                Use guest_id <strong>{selectedGuest.id}</strong> when
                creating a reservation for {getGuestFullName(selectedGuest)}.
              </p>
            ) : (
              <p className="muted-text">
                Select a guest to see the ID needed for reservations.
              </p>
            )}
          </section>
        </aside>
      </section>
    </>
  );
}
