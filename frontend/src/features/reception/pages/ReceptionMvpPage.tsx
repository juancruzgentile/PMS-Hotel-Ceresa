import { useState } from "react";

import { apiRequest } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { PageHeader } from "@/shared/components/PageHeader";
import { formatCurrencyFromCents } from "@/shared/utils/formatters";

type ApiRecord = Record<string, unknown>;

type Room = {
  id: number;
  room_number: string;
  room_status: string;
  cleaning_status: string;
  maintenance_status: string;
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

type AuditEvent = {
  id: number;
  event_type: string;
  actor_user_id: number | null;
  before_state: ApiRecord;
  after_state: ApiRecord;
  created_at: string;
};

const todayCode = new Date()
  .toISOString()
  .slice(0, 10)
  .replace(/-/g, "");
const demoRunCode = `${todayCode}-${Date.now()
  .toString(36)
  .toUpperCase()}`;
const demoShortCode = demoRunCode.slice(-10);
const demoPaymentReference = `MVP-PAY-${demoRunCode}`;

const initialGuest = {
  guest_code: `WEB-GUEST-${demoRunCode}`,
  first_name: "Demo",
  last_name: "Guest",
  email: "",
  phone: "",
  nationality: "AR",
  notes: "Created from Reception MVP.",
};

const initialRoom = {
  room_number: `WEB-${demoShortCode}`,
  floor: "1",
  room_type: "Standard",
  has_balcony: false,
  has_jacuzzi: false,
  notes: "",
};

const initialReservation = {
  reservation_code: `WEB-RES-${demoRunCode}`,
  check_in_date: "2027-06-01",
  check_out_date: "2027-06-05",
  adults: "2",
  children: "0",
  notes: "Created from Reception MVP.",
};

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

function optionalActorBody(actorUserId: string) {
  const trimmed = actorUserId.trim();

  if (trimmed === "") {
    return undefined;
  }

  const parsedActorId = Number(trimmed);

  if (!Number.isInteger(parsedActorId) || parsedActorId <= 0) {
    throw new Error("Actor user ID must be a positive integer.");
  }

  return { actor_user_id: parsedActorId };
}

function ResultBlock({
  title,
  value,
}: {
  title: string;
  value: unknown;
}) {
  if (value === null) {
    return null;
  }

  return (
    <section className="content-panel mvp-result">
      <h2>{title}</h2>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </section>
  );
}

export function ReceptionMvpPage() {
  const [guestForm, setGuestForm] = useState(initialGuest);
  const [roomForm, setRoomForm] = useState(initialRoom);
  const [reservationForm, setReservationForm] =
    useState(initialReservation);
  const [existingRoomId, setExistingRoomId] = useState("");
  const [reservationId, setReservationId] = useState("");
  const [billingAccountId, setBillingAccountId] = useState("");
  const [actorUserId, setActorUserId] = useState("");
  const [chargeAmount, setChargeAmount] = useState("50000");
  const [paymentAmount, setPaymentAmount] = useState("50000");
  const [guestId, setGuestId] = useState<number | null>(null);
  const [roomId, setRoomId] = useState<number | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [summary, setSummary] = useState<ReceptionSummary | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [lastResult, setLastResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  async function runStep<T>(
    action: () => Promise<T>,
    onSuccess?: (result: T) => void,
  ) {
    setIsBusy(true);
    setError(null);

    try {
      const result = await action();
      setLastResult(result);
      onSuccess?.(result);
    } catch (apiError) {
      setError(
        apiError instanceof Error
          ? apiError.message
          : "Unexpected API error.",
      );
    } finally {
      setIsBusy(false);
    }
  }

  const activeReservationId = Number(reservationId);
  const activeAccountId = Number(billingAccountId);

  return (
    <>
      <PageHeader
        title="Reception MVP"
        description="Run the main hotel flow from guest creation to audit review."
      />

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="mvp-layout">
        <div className="mvp-steps">
          <section className="content-panel mvp-step">
            <h2>1. Guest</h2>
            <div className="form-grid">
              <label>
                Guest code
                <input
                  value={guestForm.guest_code}
                  onChange={(event) =>
                    setGuestForm({
                      ...guestForm,
                      guest_code: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                First name
                <input
                  value={guestForm.first_name}
                  onChange={(event) =>
                    setGuestForm({
                      ...guestForm,
                      first_name: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                Last name
                <input
                  value={guestForm.last_name}
                  onChange={(event) =>
                    setGuestForm({
                      ...guestForm,
                      last_name: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                Email
                <input
                  value={guestForm.email}
                  onChange={(event) =>
                    setGuestForm({
                      ...guestForm,
                      email: event.target.value,
                    })
                  }
                />
              </label>
            </div>
            <button
              className="primary-button"
              disabled={isBusy}
              onClick={() =>
                runStep(
                  () =>
                    apiRequest<{ guest_id: number }>(
                      endpoints.guests.create,
                      {
                        method: "POST",
                        body: {
                          ...guestForm,
                          email: optionalText(guestForm.email),
                          phone: optionalText(guestForm.phone),
                          nationality: optionalText(
                            guestForm.nationality,
                          ),
                          notes: optionalText(guestForm.notes),
                        },
                      },
                    ),
                  (result) => setGuestId(result.guest_id),
                )
              }
            >
              Create guest
            </button>
          </section>

          <section className="content-panel mvp-step">
            <h2>2. Room</h2>
            <div className="form-grid">
              <label>
                Existing room
                <select
                  value={existingRoomId}
                  onChange={(event) => {
                    setExistingRoomId(event.target.value);
                    setRoomId(
                      event.target.value
                        ? Number(event.target.value)
                        : null,
                    );
                  }}
                >
                  <option value="">Create or choose a room</option>
                  {rooms.map((room) => (
                    <option key={room.id} value={room.id}>
                      {room.room_number} - {room.room_status}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Room number
                <input
                  value={roomForm.room_number}
                  onChange={(event) =>
                    setRoomForm({
                      ...roomForm,
                      room_number: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                Floor
                <input
                  type="number"
                  value={roomForm.floor}
                  onChange={(event) =>
                    setRoomForm({
                      ...roomForm,
                      floor: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                Room type
                <input
                  value={roomForm.room_type}
                  onChange={(event) =>
                    setRoomForm({
                      ...roomForm,
                      room_type: event.target.value,
                    })
                  }
                />
              </label>
            </div>
            <div className="button-row">
              <button
                className="secondary-button"
                disabled={isBusy}
                onClick={() =>
                  runStep(
                    () => apiRequest<Room[]>(endpoints.rooms.list),
                    setRooms,
                  )
                }
              >
                Load rooms
              </button>
              <button
                className="primary-button"
                disabled={isBusy}
                onClick={() =>
                  runStep(
                    () =>
                      apiRequest<{ room_id: number }>(
                        endpoints.rooms.create,
                        {
                          method: "POST",
                          body: {
                            ...roomForm,
                            floor: Number(roomForm.floor),
                            notes: optionalText(roomForm.notes),
                          },
                        },
                      ),
                    (result) => {
                      setRoomId(result.room_id);
                      setExistingRoomId(String(result.room_id));
                    },
                  )
                }
              >
                Create room
              </button>
            </div>
          </section>

          <section className="content-panel mvp-step">
            <h2>3. Reservation</h2>
            <div className="form-grid">
              <label>
                Reservation code
                <input
                  value={reservationForm.reservation_code}
                  onChange={(event) =>
                    setReservationForm({
                      ...reservationForm,
                      reservation_code: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                Check-in date
                <input
                  type="date"
                  value={reservationForm.check_in_date}
                  onChange={(event) =>
                    setReservationForm({
                      ...reservationForm,
                      check_in_date: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                Check-out date
                <input
                  type="date"
                  value={reservationForm.check_out_date}
                  onChange={(event) =>
                    setReservationForm({
                      ...reservationForm,
                      check_out_date: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                Adults
                <input
                  type="number"
                  value={reservationForm.adults}
                  onChange={(event) =>
                    setReservationForm({
                      ...reservationForm,
                      adults: event.target.value,
                    })
                  }
                />
              </label>
            </div>
            <button
              className="primary-button"
              disabled={isBusy || guestId === null || roomId === null}
              onClick={() =>
                runStep(
                  () =>
                    apiRequest<{ reservation_id: number }>(
                      endpoints.reservations.create,
                      {
                        method: "POST",
                        body: {
                          ...reservationForm,
                          guest_id: guestId,
                          room_id: roomId,
                          status: "confirmed",
                          adults: Number(reservationForm.adults),
                          children: Number(reservationForm.children),
                          notes: optionalText(reservationForm.notes),
                        },
                      },
                    ),
                  (result) =>
                    setReservationId(String(result.reservation_id)),
                )
              }
            >
              Create reservation
            </button>
          </section>

          <section className="content-panel mvp-step">
            <h2>4. Billing</h2>
            <div className="form-grid">
              <label>
                Reservation ID
                <input
                  type="number"
                  value={reservationId}
                  onChange={(event) =>
                    setReservationId(event.target.value)
                  }
                />
              </label>
              <label>
                Billing account ID
                <input
                  type="number"
                  value={billingAccountId}
                  onChange={(event) =>
                    setBillingAccountId(event.target.value)
                  }
                />
              </label>
              <label>
                Charge cents
                <input
                  type="number"
                  value={chargeAmount}
                  onChange={(event) =>
                    setChargeAmount(event.target.value)
                  }
                />
              </label>
              <label>
                Payment cents
                <input
                  type="number"
                  value={paymentAmount}
                  onChange={(event) =>
                    setPaymentAmount(event.target.value)
                  }
                />
              </label>
            </div>
            <div className="button-row">
              <button
                className="secondary-button"
                disabled={isBusy || !activeReservationId}
                onClick={() =>
                  runStep(
                    () =>
                      apiRequest<{ billing_account_id: number }>(
                        endpoints.billing.accounts,
                        {
                          method: "POST",
                          body: {
                            reservation_id: activeReservationId,
                            notes: "Created from Reception MVP.",
                          },
                        },
                      ),
                    (result) =>
                      setBillingAccountId(
                        String(result.billing_account_id),
                      ),
                  )
                }
              >
                Create account
              </button>
              <button
                className="secondary-button"
                disabled={isBusy || !activeAccountId}
                onClick={() =>
                  runStep(() =>
                    apiRequest(endpoints.billing.charges(activeAccountId), {
                      method: "POST",
                      body: {
                        source_module: "rooms",
                        description: "Accommodation package",
                        amount_cents: Number(chargeAmount),
                      },
                    }),
                  )
                }
              >
                Add charge
              </button>
              <button
                className="secondary-button"
                disabled={isBusy || !activeAccountId}
                onClick={() =>
                  runStep(() =>
                    apiRequest(
                      endpoints.billing.payments(activeAccountId),
                      {
                        method: "POST",
                        body: {
                          payment_method: "card",
                          amount_cents: Number(paymentAmount),
                          reference: demoPaymentReference,
                        },
                      },
                    ),
                  )
                }
              >
                Register payment
              </button>
            </div>
          </section>

          <section className="content-panel mvp-step">
            <h2>5. Reception</h2>
            <div className="form-grid">
              <label>
                Optional actor user ID
                <input
                  type="number"
                  value={actorUserId}
                  onChange={(event) =>
                    setActorUserId(event.target.value)
                  }
                />
              </label>
            </div>
            <div className="button-row">
              <button
                className="secondary-button"
                disabled={isBusy || !activeReservationId}
                onClick={() =>
                  runStep(
                    () =>
                      apiRequest<ReceptionSummary>(
                        endpoints.reception.summary(activeReservationId),
                      ),
                    setSummary,
                  )
                }
              >
                Load summary
              </button>
              <button
                className="primary-button"
                disabled={isBusy || !activeReservationId}
                onClick={() =>
                  runStep(() =>
                    apiRequest(
                      endpoints.reception.checkIn(activeReservationId),
                      {
                        method: "POST",
                        body: optionalActorBody(actorUserId),
                      },
                    ),
                  )
                }
              >
                Check-in
              </button>
              <button
                className="primary-button"
                disabled={isBusy || !activeReservationId}
                onClick={() =>
                  runStep(() =>
                    apiRequest(
                      endpoints.reception.checkOut(activeReservationId),
                      {
                        method: "POST",
                        body: optionalActorBody(actorUserId),
                      },
                    ),
                  )
                }
              >
                Check-out
              </button>
              <button
                className="secondary-button"
                disabled={isBusy || !activeReservationId}
                onClick={() =>
                  runStep(
                    () =>
                      apiRequest<AuditEvent[]>(
                        endpoints.reception.events(activeReservationId),
                      ),
                    setEvents,
                  )
                }
              >
                Load audit events
              </button>
            </div>
          </section>
        </div>

        <aside className="mvp-sidebar">
          <section className="content-panel mvp-summary">
            <h2>Current IDs</h2>
            <dl>
              <div>
                <dt>Guest</dt>
                <dd>{guestId ?? "-"}</dd>
              </div>
              <div>
                <dt>Room</dt>
                <dd>{roomId ?? "-"}</dd>
              </div>
              <div>
                <dt>Reservation</dt>
                <dd>{reservationId || "-"}</dd>
              </div>
              <div>
                <dt>Billing account</dt>
                <dd>{billingAccountId || "-"}</dd>
              </div>
            </dl>
          </section>

          {summary ? (
            <section className="content-panel mvp-summary">
              <h2>Reception summary</h2>
              <p>
                {summary.reservation.reservation_code} -{" "}
                {summary.reservation.status}
              </p>
              <p>
                {summary.reservation.guest_first_name}{" "}
                {summary.reservation.guest_last_name} in room{" "}
                {summary.reservation.room_number}
              </p>
              {summary.billing_account ? (
                <p>
                  Balance:{" "}
                  {formatCurrencyFromCents(
                    summary.billing_account.balance_cents,
                    summary.billing_account.currency,
                  )}
                </p>
              ) : (
                <p>No billing account.</p>
              )}
            </section>
          ) : null}

          <section className="content-panel mvp-summary">
            <h2>Audit events</h2>
            {events.length === 0 ? (
              <p>No events loaded.</p>
            ) : (
              <ol className="audit-list">
                {events.map((event) => (
                  <li key={event.id}>
                    <strong>{event.event_type}</strong>
                    <span>Actor: {event.actor_user_id ?? "none"}</span>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <ResultBlock title="Last API result" value={lastResult} />
        </aside>
      </section>
    </>
  );
}
