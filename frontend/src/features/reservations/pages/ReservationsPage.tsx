import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { apiRequest } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { EmptyState } from "@/shared/components/EmptyState";
import { PageHeader } from "@/shared/components/PageHeader";
import { formatCurrencyFromCents } from "@/shared/utils/formatters";

type Reservation = {
  id: number;
  reservation_code: string;
  guest_id: number;
  guest_code: string;
  guest_first_name: string;
  guest_last_name: string;
  room_id: number;
  room_number: string;
  check_in_date: string;
  check_out_date: string;
  status: string;
  adults: number;
  children: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

type ReceptionSummary = {
  reservation: {
    id: number;
    reservation_code: string;
    status: string;
    room_number: string;
    guest_first_name: string;
    guest_last_name: string;
  };
  billing_enabled: boolean;
  billing_account: {
    id: number;
    status: string;
    balance_cents: number;
    currency: string;
    charges_total_cents: number;
    payments_total_cents: number;
  } | null;
};

function getGuestFullName(reservation: Reservation): string {
  return `${reservation.guest_first_name} ${reservation.guest_last_name}`;
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected API error.";
}

export function ReservationsPage() {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [selectedReservation, setSelectedReservation] =
    useState<Reservation | null>(null);
  const [summary, setSummary] = useState<ReceptionSummary | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  async function loadReservations() {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiRequest<Reservation[]>(
        endpoints.reservations.list,
      );

      setReservations(data);
      setLastMessage(`${data.length} reservation(s) loaded.`);

      if (selectedReservation) {
        const refreshedSelection = data.find(
          (reservation) => reservation.id === selectedReservation.id,
        );
        setSelectedReservation(refreshedSelection ?? null);
      }
    } catch (loadError) {
      setError(`API error: ${getErrorMessage(loadError)}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadReservations();
    // Initial page load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const statusOptions = useMemo(
    () =>
      Array.from(
        new Set(reservations.map((reservation) => reservation.status)),
      ).sort(),
    [reservations],
  );

  const filteredReservations = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return reservations.filter((reservation) => {
      const matchesStatus =
        statusFilter === "" || reservation.status === statusFilter;
      const matchesSearch =
        normalizedSearch === "" ||
        reservation.reservation_code
          .toLowerCase()
          .includes(normalizedSearch) ||
        getGuestFullName(reservation)
          .toLowerCase()
          .includes(normalizedSearch) ||
        reservation.room_number.toLowerCase().includes(normalizedSearch);

      return matchesStatus && matchesSearch;
    });
  }, [reservations, searchTerm, statusFilter]);

  async function selectReservation(reservation: Reservation) {
    setIsDetailLoading(true);
    setError(null);
    setSummary(null);

    try {
      const detail = await apiRequest<Reservation>(
        endpoints.reservations.detail(reservation.id),
      );

      setSelectedReservation(detail);
      setLastMessage(`Reservation ${detail.reservation_code} selected.`);
    } catch (detailError) {
      setError(`API error: ${getErrorMessage(detailError)}`);
    } finally {
      setIsDetailLoading(false);
    }
  }

  async function loadReceptionSummary() {
    if (!selectedReservation) {
      setError("Select a reservation before loading Reception summary.");
      return;
    }

    setIsSummaryLoading(true);
    setError(null);

    try {
      const data = await apiRequest<ReceptionSummary>(
        endpoints.reception.summary(selectedReservation.id),
      );

      setSummary(data);
      setLastMessage(
        `Reception summary loaded for ${data.reservation.reservation_code}.`,
      );
    } catch (summaryError) {
      setError(`API error: ${getErrorMessage(summaryError)}`);
    } finally {
      setIsSummaryLoading(false);
    }
  }

  async function copyReservationId() {
    if (!selectedReservation) {
      return;
    }

    try {
      await navigator.clipboard.writeText(String(selectedReservation.id));
      setLastMessage(`reservation_id ${selectedReservation.id} copied.`);
    } catch {
      setLastMessage(
        `reservation_id ${selectedReservation.id} is ready to copy manually.`,
      );
    }
  }

  return (
    <>
      <PageHeader
        title="Reservations"
        description="List, search and inspect existing hotel reservations."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {lastMessage ? (
        <div className="success-banner">{lastMessage}</div>
      ) : null}

      <section className="reservations-layout">
        <div className="reservations-main">
          <section className="content-panel">
            <div className="panel-heading">
              <div>
                <h2>Reservation list</h2>
                <p>
                  Search locally by code, guest name or room number.
                </p>
              </div>
              <button
                className="secondary-button"
                disabled={isLoading}
                onClick={() => void loadReservations()}
              >
                Refresh
              </button>
            </div>

            <div className="reservations-toolbar">
              <label>
                Search
                <input
                  placeholder="Code, guest or room"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                />
              </label>
              <label>
                Status
                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(event.target.value)
                  }
                >
                  <option value="">All statuses</option>
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {isLoading ? (
              <p className="muted-text">Loading reservations...</p>
            ) : reservations.length === 0 ? (
              <EmptyState
                title="No reservations yet"
                message="Create a reservation from Reception MVP or another workflow, then refresh this list."
              />
            ) : filteredReservations.length === 0 ? (
              <EmptyState
                title="No matches"
                message="Adjust the search text or status filter."
              />
            ) : (
              <div className="reservations-table">
                <div className="reservations-table-row reservations-table-head">
                  <span>ID</span>
                  <span>Code</span>
                  <span>Guest</span>
                  <span>Room</span>
                  <span>Check-in</span>
                  <span>Check-out</span>
                  <span>Status</span>
                  <span>Adults</span>
                  <span>Children</span>
                </div>
                {filteredReservations.map((reservation) => (
                  <button
                    className={`reservations-table-row ${
                      selectedReservation?.id === reservation.id
                        ? "selected"
                        : ""
                    }`}
                    key={reservation.id}
                    onClick={() => void selectReservation(reservation)}
                  >
                    <span>{reservation.id}</span>
                    <span>{reservation.reservation_code}</span>
                    <span>{getGuestFullName(reservation)}</span>
                    <span>{reservation.room_number}</span>
                    <span>{reservation.check_in_date}</span>
                    <span>{reservation.check_out_date}</span>
                    <span>{reservation.status}</span>
                    <span>{reservation.adults}</span>
                    <span>{reservation.children}</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>

        <aside className="reservations-detail">
          <section className="content-panel mvp-summary">
            <h2>Reservation detail</h2>
            {isDetailLoading ? (
              <p className="muted-text">Loading detail...</p>
            ) : selectedReservation ? (
              <>
                <dl>
                  <div>
                    <dt>ID</dt>
                    <dd>{selectedReservation.id}</dd>
                  </div>
                  <div>
                    <dt>Code</dt>
                    <dd>{selectedReservation.reservation_code}</dd>
                  </div>
                  <div>
                    <dt>Guest</dt>
                    <dd>{getGuestFullName(selectedReservation)}</dd>
                  </div>
                  <div>
                    <dt>Room</dt>
                    <dd>{selectedReservation.room_number}</dd>
                  </div>
                  <div>
                    <dt>Stay</dt>
                    <dd>
                      {selectedReservation.check_in_date} to{" "}
                      {selectedReservation.check_out_date}
                    </dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{selectedReservation.status}</dd>
                  </div>
                  <div>
                    <dt>Guests</dt>
                    <dd>
                      {selectedReservation.adults} adult(s),{" "}
                      {selectedReservation.children} child(ren)
                    </dd>
                  </div>
                </dl>

                <div className="detail-actions">
                  <button
                    className="secondary-button"
                    disabled={isSummaryLoading}
                    onClick={() => void loadReceptionSummary()}
                  >
                    Load Reception summary
                  </button>
                  <button
                    className="secondary-button"
                    onClick={() => void copyReservationId()}
                  >
                    Copy reservation ID
                  </button>
                  <Link className="text-link" to="/reception-mvp">
                    Open in Reception MVP
                  </Link>
                </div>
              </>
            ) : (
              <p className="muted-text">
                Select a reservation to inspect its details.
              </p>
            )}
          </section>

          <section className="content-panel mvp-summary">
            <h2>Reception summary</h2>
            {isSummaryLoading ? (
              <p className="muted-text">Loading summary...</p>
            ) : summary ? (
              <dl>
                <div>
                  <dt>Reservation</dt>
                  <dd>{summary.reservation.status}</dd>
                </div>
                <div>
                  <dt>Billing enabled</dt>
                  <dd>{summary.billing_enabled ? "Yes" : "No"}</dd>
                </div>
                <div>
                  <dt>Billing status</dt>
                  <dd>{summary.billing_account?.status ?? "-"}</dd>
                </div>
                <div>
                  <dt>Balance</dt>
                  <dd>
                    {summary.billing_account
                      ? formatCurrencyFromCents(
                          summary.billing_account.balance_cents,
                          summary.billing_account.currency,
                        )
                      : "-"}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="muted-text">
                Load summary to see reception and billing state.
              </p>
            )}
          </section>
        </aside>
      </section>
    </>
  );
}
