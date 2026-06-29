import { useState } from "react";

import { apiRequest } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { PageHeader } from "@/shared/components/PageHeader";
import { formatCurrencyFromCents } from "@/shared/utils/formatters";

type ApiRecord = Record<string, unknown>;
type StepStatus = "complete" | "current" | "pending";

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
  billing_account: BillingAccount | null;
};

type BillingAccount = {
  id: number;
  status: string;
  balance_cents: number;
  currency: string;
  charges_total_cents: number;
  payments_total_cents: number;
};

type BillingAccountDetail = BillingAccount & {
  charges?: unknown[];
  payments?: unknown[];
};

type AuditEvent = {
  id: number;
  event_type: string;
  actor_user_id: number | null;
  before_state: ApiRecord;
  after_state: ApiRecord;
  created_at: string;
};

type DemoCodes = {
  runCode: string;
  shortCode: string;
  guestCode: string;
  roomNumber: string;
  reservationCode: string;
  paymentReference: string;
};

type LastOutcome = {
  title: string;
  message: string;
  details?: unknown;
} | null;

type ReceptionRefresh = {
  summary: ReceptionSummary;
  events: AuditEvent[];
};

type ReceptionActionResult = {
  actionResult: ApiRecord;
  refresh: ReceptionRefresh | null;
  refreshError: string | null;
};

class LocalValidationError extends Error {}

function createDemoCodes(): DemoCodes {
  const todayCode = new Date()
    .toISOString()
    .slice(0, 10)
    .replace(/-/g, "");
  const runCode = `${todayCode}-${Date.now()
    .toString(36)
    .toUpperCase()}`;
  const shortCode = runCode.slice(-10);

  return {
    runCode,
    shortCode,
    guestCode: `WEB-GUEST-${runCode}`,
    roomNumber: `WEB-${shortCode}`,
    reservationCode: `WEB-RES-${runCode}`,
    paymentReference: `MVP-PAY-${runCode}`,
  };
}

function createGuest(codes: DemoCodes) {
  return {
    guest_code: codes.guestCode,
    first_name: "Demo",
    last_name: "Guest",
    email: "",
    phone: "",
    nationality: "AR",
    notes: "Created from Reception MVP.",
  };
}

function createRoom(codes: DemoCodes) {
  return {
    room_number: codes.roomNumber,
    floor: "1",
    room_type: "Standard",
    has_balcony: false,
    has_jacuzzi: false,
    notes: "",
  };
}

function createReservation(codes: DemoCodes) {
  return {
    reservation_code: codes.reservationCode,
    check_in_date: "2027-06-01",
    check_out_date: "2027-06-05",
    adults: "2",
    children: "0",
    notes: "Created from Reception MVP.",
  };
}

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

function parsePositiveInteger(value: string, label: string): number {
  const trimmed = value.trim();
  const parsedValue = Number(trimmed);

  if (
    trimmed === "" ||
    !Number.isInteger(parsedValue) ||
    parsedValue <= 0
  ) {
    throw new LocalValidationError(`${label} must be a positive integer.`);
  }

  return parsedValue;
}

function parseNonNegativeInteger(value: string, label: string): number {
  const trimmed = value.trim();
  const parsedValue = Number(trimmed);

  if (
    trimmed === "" ||
    !Number.isInteger(parsedValue) ||
    parsedValue < 0
  ) {
    throw new LocalValidationError(
      `${label} must be zero or a positive integer.`,
    );
  }

  return parsedValue;
}

function parseAmount(value: string, label: string): number {
  const parsedAmount = parsePositiveInteger(value, label);

  if (parsedAmount > 100_000_000) {
    throw new LocalValidationError(`${label} is too large for a demo run.`);
  }

  return parsedAmount;
}

function optionalActorBody(actorUserId: string) {
  const trimmed = actorUserId.trim();

  if (trimmed === "") {
    return undefined;
  }

  return { actor_user_id: parsePositiveInteger(trimmed, "Actor user ID") };
}

function requireKnownId(value: number | null, label: string): number {
  if (value === null) {
    throw new LocalValidationError(`${label} is required first.`);
  }

  return value;
}

function getStepStatus(
  isComplete: boolean,
  isCurrent: boolean,
): StepStatus {
  if (isComplete) {
    return "complete";
  }

  return isCurrent ? "current" : "pending";
}

function FlowGuide({
  steps,
}: {
  steps: { label: string; status: StepStatus; detail: string }[];
}) {
  return (
    <section className="content-panel mvp-flow-panel">
      <h2>Manual test flow</h2>
      <ol className="mvp-flow">
        {steps.map((step) => (
          <li className={`mvp-flow-item ${step.status}`} key={step.label}>
            <span className="mvp-flow-marker" aria-hidden="true" />
            <div>
              <strong>{step.label}</strong>
              <span>{step.detail}</span>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function ResultBlock({ outcome }: { outcome: LastOutcome }) {
  if (outcome === null) {
    return null;
  }

  return (
    <section className="content-panel mvp-result">
      <h2>{outcome.title}</h2>
      <p>{outcome.message}</p>
      {outcome.details === undefined ? null : (
        <details>
          <summary>Raw response</summary>
          <pre>{JSON.stringify(outcome.details, null, 2)}</pre>
        </details>
      )}
    </section>
  );
}

function FieldHint({ children }: { children: string }) {
  return <p className="field-hint">{children}</p>;
}

const howToTestSteps = [
  "Create guest.",
  "Create room.",
  "Create reservation.",
  "Create billing account.",
  "Add charge.",
  "Register payment for same amount.",
  "Load summary.",
  "Check-in.",
  "Check-out.",
  "Load audit events.",
];

export function ReceptionMvpPage() {
  const [demoCodes, setDemoCodes] = useState(() => createDemoCodes());
  const [guestForm, setGuestForm] = useState(() =>
    createGuest(demoCodes),
  );
  const [roomForm, setRoomForm] = useState(() => createRoom(demoCodes));
  const [reservationForm, setReservationForm] = useState(() =>
    createReservation(demoCodes),
  );
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
  const [accountSnapshot, setAccountSnapshot] =
    useState<BillingAccountDetail | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [lastOutcome, setLastOutcome] = useState<LastOutcome>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [chargeCreated, setChargeCreated] = useState(false);
  const [paymentCreated, setPaymentCreated] = useState(false);
  const [checkInDone, setCheckInDone] = useState(false);
  const [checkOutDone, setCheckOutDone] = useState(false);
  const [lastStepCompleted, setLastStepCompleted] = useState("Not started");

  async function runStep<T>(
    action: () => Promise<T>,
    onSuccess: (result: T) => LastOutcome | void,
  ) {
    setIsBusy(true);
    setError(null);

    try {
      const result = await action();
      const outcome = onSuccess(result);

      if (outcome) {
        setLastOutcome(outcome);
      }
    } catch (apiError) {
      if (apiError instanceof LocalValidationError) {
        setError(`Validation: ${apiError.message}`);
      } else {
        setError(
          apiError instanceof Error
            ? `API error: ${apiError.message}`
            : "API error: Unexpected response.",
        );
      }
    } finally {
      setIsBusy(false);
    }
  }

  function regenerateDemoCodes() {
    const nextCodes = createDemoCodes();

    setDemoCodes(nextCodes);
    setGuestForm(createGuest(nextCodes));
    setRoomForm(createRoom(nextCodes));
    setReservationForm(createReservation(nextCodes));
    setExistingRoomId("");
    setReservationId("");
    setBillingAccountId("");
    setSummary(null);
    setAccountSnapshot(null);
    setEvents([]);
    setLastOutcome({
      title: "Demo codes regenerated",
      message:
        "The form now uses fresh guest, room, reservation, and payment references.",
      details: nextCodes,
    });
    setError(null);
    setChargeCreated(false);
    setPaymentCreated(false);
    setCheckInDone(false);
    setCheckOutDone(false);
    setLastStepCompleted("Demo codes regenerated");
  }

  function resetDemoFlow() {
    const nextCodes = createDemoCodes();

    setDemoCodes(nextCodes);
    setGuestForm(createGuest(nextCodes));
    setRoomForm(createRoom(nextCodes));
    setReservationForm(createReservation(nextCodes));
    setExistingRoomId("");
    setReservationId("");
    setBillingAccountId("");
    setGuestId(null);
    setRoomId(null);
    setSummary(null);
    setAccountSnapshot(null);
    setEvents([]);
    setLastOutcome(null);
    setError(null);
    setChargeCreated(false);
    setPaymentCreated(false);
    setCheckInDone(false);
    setCheckOutDone(false);
    setLastStepCompleted("Reset demo flow");
  }

  async function loadSummaryAndEvents(
    activeReservationId: number,
  ): Promise<ReceptionRefresh> {
    const [nextSummary, nextEvents] = await Promise.all([
      apiRequest<ReceptionSummary>(
        endpoints.reception.summary(activeReservationId),
      ),
      apiRequest<AuditEvent[]>(
        endpoints.reception.events(activeReservationId),
      ),
    ]);

    return {
      summary: nextSummary,
      events: nextEvents,
    };
  }

  function applyReceptionRefresh(refresh: ReceptionRefresh) {
    setSummary(refresh.summary);
    setEvents(refresh.events);
  }

  const currentReservationId = reservationId.trim()
    ? Number(reservationId)
    : null;
  const currentAccountId = billingAccountId.trim()
    ? Number(billingAccountId)
    : null;
  const currentBalance =
    summary?.billing_account?.balance_cents ??
    accountSnapshot?.balance_cents ??
    null;
  const currentCurrency =
    summary?.billing_account?.currency ?? accountSnapshot?.currency ?? "ARS";
  const currentBillingAccountStatus =
    summary?.billing_account?.status ?? accountSnapshot?.status ?? "-";
  const currentReservationStatus = summary?.reservation.status ?? "-";
  const checkoutBalanceWarning =
    summary !== null && currentBalance !== null && currentBalance > 0;

  const flowSteps = [
    {
      label: "Guest",
      status: getStepStatus(guestId !== null, guestId === null),
      detail:
        guestId === null ? "Create a demo guest." : `guest_id ${guestId}`,
    },
    {
      label: "Room",
      status: getStepStatus(roomId !== null, guestId !== null),
      detail: roomId === null ? "Create or choose a room." : `room_id ${roomId}`,
    },
    {
      label: "Reservation",
      status: getStepStatus(
        reservationId.trim() !== "",
        guestId !== null && roomId !== null,
      ),
      detail:
        reservationId.trim() === ""
          ? "Needs guest_id and room_id."
          : `reservation_id ${reservationId}`,
    },
    {
      label: "Billing account",
      status: getStepStatus(
        billingAccountId.trim() !== "",
        reservationId.trim() !== "",
      ),
      detail:
        billingAccountId.trim() === ""
          ? "Needs reservation_id."
          : `account_id ${billingAccountId}`,
    },
    {
      label: "Charge",
      status: getStepStatus(chargeCreated, billingAccountId.trim() !== ""),
      detail: chargeCreated ? "Charge added." : "Needs account_id.",
    },
    {
      label: "Payment",
      status: getStepStatus(paymentCreated, billingAccountId.trim() !== ""),
      detail: paymentCreated ? "Payment registered." : "Needs account_id.",
    },
    {
      label: "Summary",
      status: getStepStatus(summary !== null, reservationId.trim() !== ""),
      detail: summary ? "Summary loaded." : "Load reservation summary.",
    },
    {
      label: "Check-in",
      status: getStepStatus(checkInDone, reservationId.trim() !== ""),
      detail: checkInDone ? "Guest checked in." : "Needs reservation_id.",
    },
    {
      label: "Check-out",
      status: getStepStatus(checkOutDone, reservationId.trim() !== ""),
      detail: checkOutDone ? "Guest checked out." : "Needs reservation_id.",
    },
    {
      label: "Audit events",
      status: getStepStatus(events.length > 0, reservationId.trim() !== ""),
      detail:
        events.length > 0
          ? `${events.length} event(s) loaded.`
          : "Load events after reception actions.",
    },
  ];

  return (
    <>
      <PageHeader
        title="Reception MVP"
        description="Run the main hotel flow from guest creation to audit review."
      />

      {error ? <div className="error-banner">{error}</div> : null}

      <FlowGuide steps={flowSteps} />

      <section className="mvp-layout">
        <div className="mvp-steps">
          <section className="content-panel mvp-step">
            <div className="panel-heading">
              <div>
                <h2>How to test</h2>
                <p>Use this order for the full manual Reception MVP path.</p>
              </div>
            </div>
            <ol className="how-to-test-list">
              {howToTestSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <div className="button-row">
              <button
                className="secondary-button"
                disabled={isBusy}
                onClick={resetDemoFlow}
              >
                Reset demo flow
              </button>
              <button
                className="secondary-button"
                disabled={isBusy}
                onClick={() =>
                  runStep(
                    () =>
                      loadSummaryAndEvents(
                        parsePositiveInteger(
                          reservationId,
                          "reservation_id",
                        ),
                      ),
                    (result) => {
                      applyReceptionRefresh(result);
                      setLastStepCompleted(
                        "Reload summary and events",
                      );
                      return {
                        title: "Summary and audit events reloaded",
                        message: `${result.events.length} audit event(s) are now visible for this reservation.`,
                        details: result,
                      };
                    },
                  )
                }
              >
                Reload summary and events
              </button>
            </div>
          </section>

          <section className="content-panel mvp-step">
            <div className="panel-heading">
              <div>
                <h2>1. Guest</h2>
                <p>Create the guest record used by the demo reservation.</p>
              </div>
              <span className="status-pill status-clean">
                {guestId === null ? "Pending" : "Done"}
              </span>
            </div>
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
                  (result) => {
                    setGuestId(result.guest_id);
                    setLastStepCompleted("Create guest");
                    return {
                      title: "Guest created",
                      message: `guest_id ${result.guest_id} is ready for the reservation.`,
                      details: result,
                    };
                  },
                )
              }
            >
              Create guest
            </button>
          </section>

          <section className="content-panel mvp-step">
            <div className="panel-heading">
              <div>
                <h2>2. Room</h2>
                <p>Create a demo room or reuse one already loaded.</p>
              </div>
              <span className="status-pill status-clean">
                {roomId === null ? "Pending" : "Done"}
              </span>
            </div>
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
                    (result) => {
                      setRooms(result);
                      setLastStepCompleted("Load rooms");
                      return {
                        title: "Rooms loaded",
                        message: `${result.length} room(s) available to choose from.`,
                      };
                    },
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
                    () => {
                      const floor = parsePositiveInteger(
                        roomForm.floor,
                        "Floor",
                      );

                      return apiRequest<{ room_id: number }>(
                        endpoints.rooms.create,
                        {
                          method: "POST",
                          body: {
                            ...roomForm,
                            floor,
                            notes: optionalText(roomForm.notes),
                          },
                        },
                      );
                    },
                    (result) => {
                      setRoomId(result.room_id);
                      setExistingRoomId(String(result.room_id));
                      setLastStepCompleted("Create room");
                      return {
                        title: "Room created",
                        message: `room_id ${result.room_id} is ready for the reservation.`,
                        details: result,
                      };
                    },
                  )
                }
              >
                Create room
              </button>
            </div>
          </section>

          <section className="content-panel mvp-step">
            <div className="panel-heading">
              <div>
                <h2>3. Reservation</h2>
                <p>Connect the guest and room before continuing.</p>
              </div>
              <span className="status-pill status-clean">
                {reservationId.trim() === "" ? "Pending" : "Done"}
              </span>
            </div>
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
            <FieldHint>
              Requires a guest_id and room_id. Current values are shown in
              the sidebar.
            </FieldHint>
            <button
              className="primary-button"
              disabled={isBusy || guestId === null || roomId === null}
              onClick={() =>
                runStep(
                  () => {
                    const activeGuestId = requireKnownId(
                      guestId,
                      "guest_id",
                    );
                    const activeRoomId = requireKnownId(roomId, "room_id");

                    return apiRequest<{ reservation_id: number }>(
                      endpoints.reservations.create,
                      {
                        method: "POST",
                        body: {
                          ...reservationForm,
                          guest_id: activeGuestId,
                          room_id: activeRoomId,
                          status: "confirmed",
                          adults: parsePositiveInteger(
                            reservationForm.adults,
                            "Adults",
                          ),
                          children: parseNonNegativeInteger(
                            reservationForm.children,
                            "Children",
                          ),
                          notes: optionalText(reservationForm.notes),
                        },
                      },
                    );
                  },
                  (result) => {
                    setReservationId(String(result.reservation_id));
                    setLastStepCompleted("Create reservation");
                    return {
                      title: "Reservation created",
                      message: `reservation_id ${result.reservation_id} is ready for billing and reception.`,
                      details: result,
                    };
                  },
                )
              }
            >
              Create reservation
            </button>
          </section>

          <section className="content-panel mvp-step">
            <div className="panel-heading">
              <div>
                <h2>4. Billing</h2>
                <p>Create the account, add the charge, then register payment.</p>
              </div>
              <span className="status-pill status-clean">
                {paymentCreated ? "Paid" : "Pending"}
              </span>
            </div>
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
                disabled={isBusy || reservationId.trim() === ""}
                onClick={() =>
                  runStep(
                    () =>
                      apiRequest<{ billing_account_id: number }>(
                        endpoints.billing.accounts,
                        {
                          method: "POST",
                          body: {
                            reservation_id: parsePositiveInteger(
                              reservationId,
                              "reservation_id",
                            ),
                            notes: "Created from Reception MVP.",
                          },
                        },
                      ),
                    (result) => {
                      setBillingAccountId(
                        String(result.billing_account_id),
                      );
                      setLastStepCompleted("Create billing account");
                      return {
                        title: "Billing account created",
                        message: `account_id ${result.billing_account_id} is ready for charges and payments.`,
                        details: result,
                      };
                    },
                  )
                }
              >
                Create account
              </button>
              <button
                className="secondary-button"
                disabled={isBusy || billingAccountId.trim() === ""}
                onClick={() =>
                  runStep(
                    async () => {
                      const accountId = parsePositiveInteger(
                        billingAccountId,
                        "billing_account_id",
                      );

                      await apiRequest(
                        endpoints.billing.charges(accountId),
                        {
                          method: "POST",
                          body: {
                            source_module: "rooms",
                            description: "Accommodation package",
                            amount_cents: parseAmount(
                              chargeAmount,
                              "Charge amount",
                            ),
                          },
                        },
                      );

                      return apiRequest<BillingAccountDetail>(
                        endpoints.billing.account(accountId),
                      );
                    },
                    (result) => {
                      setChargeCreated(true);
                      setAccountSnapshot(result);
                      setLastStepCompleted("Add charge");
                      return {
                        title: "Charge added",
                        message: `Balance is now ${formatCurrencyFromCents(
                          result.balance_cents,
                          result.currency,
                        )}.`,
                        details: result,
                      };
                    },
                  )
                }
              >
                Add charge
              </button>
              <button
                className="secondary-button"
                disabled={isBusy || billingAccountId.trim() === ""}
                onClick={() =>
                  runStep(
                    async () => {
                      const accountId = parsePositiveInteger(
                        billingAccountId,
                        "billing_account_id",
                      );

                      await apiRequest(
                        endpoints.billing.payments(accountId),
                        {
                          method: "POST",
                          body: {
                            payment_method: "card",
                            amount_cents: parseAmount(
                              paymentAmount,
                              "Payment amount",
                            ),
                            reference: demoCodes.paymentReference,
                          },
                        },
                      );

                      return apiRequest<BillingAccountDetail>(
                        endpoints.billing.account(accountId),
                      );
                    },
                    (result) => {
                      setPaymentCreated(true);
                      setAccountSnapshot(result);
                      setLastStepCompleted("Register payment");
                      return {
                        title: "Payment registered",
                        message: `Balance is now ${formatCurrencyFromCents(
                          result.balance_cents,
                          result.currency,
                        )}.`,
                        details: result,
                      };
                    },
                  )
                }
              >
                Register payment
              </button>
            </div>
          </section>

          <section className="content-panel mvp-step">
            <div className="panel-heading">
              <div>
                <h2>5. Reception</h2>
                <p>Load summary, check in, check out, then inspect audit events.</p>
              </div>
              <span className="status-pill status-clean">
                {checkOutDone ? "Checked out" : "Pending"}
              </span>
            </div>
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
            <FieldHint>
              Actor user ID is manual traceability only; it is not real
              authentication.
            </FieldHint>
            {checkoutBalanceWarning ? (
              <div className="warning-banner">
                The current summary shows an open balance. Check-out may
                fail until payment brings the balance to zero.
              </div>
            ) : null}
            <div className="button-row">
              <button
                className="secondary-button"
                disabled={isBusy || reservationId.trim() === ""}
                onClick={() =>
                  runStep(
                    () =>
                      apiRequest<ReceptionSummary>(
                        endpoints.reception.summary(
                          parsePositiveInteger(
                            reservationId,
                            "reservation_id",
                          ),
                        ),
                      ),
                    (result) => {
                      setSummary(result);
                      setLastStepCompleted("Load summary");
                      return {
                        title: "Summary loaded",
                        message: `${result.reservation.reservation_code} is ${result.reservation.status}.`,
                        details: result,
                      };
                    },
                  )
                }
              >
                Load summary
              </button>
              <button
                className="primary-button"
                disabled={isBusy || reservationId.trim() === ""}
                onClick={() =>
                  runStep(
                    async (): Promise<ReceptionActionResult> => {
                      const activeReservationId = parsePositiveInteger(
                        reservationId,
                        "reservation_id",
                      );
                      const actionResult = await apiRequest<ApiRecord>(
                        endpoints.reception.checkIn(activeReservationId),
                        {
                          method: "POST",
                          body: optionalActorBody(actorUserId),
                        },
                      );

                      try {
                        return {
                          actionResult,
                          refresh:
                            await loadSummaryAndEvents(
                              activeReservationId,
                            ),
                          refreshError: null,
                        };
                      } catch (refreshError) {
                        return {
                          actionResult,
                          refresh: null,
                          refreshError:
                            refreshError instanceof Error
                              ? refreshError.message
                              : "Summary/events refresh failed.",
                        };
                      }
                    },
                    (result) => {
                      setCheckInDone(true);
                      setLastStepCompleted("Check-in");

                      if (result.refresh) {
                        applyReceptionRefresh(result.refresh);
                      }

                      return {
                        title: "Check-in completed",
                        message: result.refreshError
                          ? `Check-in worked, but summary/events refresh failed: ${result.refreshError}`
                          : "Check-in worked and summary/events were refreshed.",
                        details: result.actionResult,
                      };
                    },
                  )
                }
              >
                Check-in
              </button>
              <button
                className="primary-button"
                disabled={isBusy || reservationId.trim() === ""}
                onClick={() =>
                  runStep(
                    async (): Promise<ReceptionActionResult> => {
                      const activeReservationId = parsePositiveInteger(
                        reservationId,
                        "reservation_id",
                      );
                      const actionResult = await apiRequest<ApiRecord>(
                        endpoints.reception.checkOut(activeReservationId),
                        {
                          method: "POST",
                          body: optionalActorBody(actorUserId),
                        },
                      );

                      try {
                        return {
                          actionResult,
                          refresh:
                            await loadSummaryAndEvents(
                              activeReservationId,
                            ),
                          refreshError: null,
                        };
                      } catch (refreshError) {
                        return {
                          actionResult,
                          refresh: null,
                          refreshError:
                            refreshError instanceof Error
                              ? refreshError.message
                              : "Summary/events refresh failed.",
                        };
                      }
                    },
                    (result) => {
                      setCheckOutDone(true);
                      setLastStepCompleted("Check-out");

                      if (result.refresh) {
                        applyReceptionRefresh(result.refresh);
                      }

                      return {
                        title: "Check-out completed",
                        message: result.refreshError
                          ? `Check-out worked, but summary/events refresh failed: ${result.refreshError}`
                          : "Check-out worked and summary/events were refreshed.",
                        details: result.actionResult,
                      };
                    },
                  )
                }
              >
                Check-out
              </button>
              <button
                className="secondary-button"
                disabled={isBusy || reservationId.trim() === ""}
                onClick={() =>
                  runStep(
                    () =>
                      apiRequest<AuditEvent[]>(
                        endpoints.reception.events(
                          parsePositiveInteger(
                            reservationId,
                            "reservation_id",
                          ),
                        ),
                      ),
                    (result) => {
                      setEvents(result);
                      setLastStepCompleted("Load audit events");
                      return {
                        title: "Audit events loaded",
                        message: `${result.length} audit event(s) found for this reservation.`,
                      };
                    },
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
            <h2>Operational status</h2>
            <dl>
              <div>
                <dt>Reservation status</dt>
                <dd>{currentReservationStatus}</dd>
              </div>
              <div>
                <dt>Billing status</dt>
                <dd>{currentBillingAccountStatus}</dd>
              </div>
              <div>
                <dt>Balance</dt>
                <dd>
                  {currentBalance === null
                    ? "-"
                    : formatCurrencyFromCents(
                        currentBalance,
                        currentCurrency,
                      )}
                </dd>
              </div>
              <div>
                <dt>Audit events</dt>
                <dd>{events.length}</dd>
              </div>
              <div>
                <dt>Last completed</dt>
                <dd>{lastStepCompleted}</dd>
              </div>
            </dl>
          </section>

          <section className="content-panel mvp-summary">
            <div className="panel-heading compact">
              <div>
                <h2>Demo codes</h2>
                <p>Use fresh codes to avoid collisions during manual tests.</p>
              </div>
            </div>
            <dl>
              <div>
                <dt>Guest</dt>
                <dd>{demoCodes.guestCode}</dd>
              </div>
              <div>
                <dt>Room</dt>
                <dd>{demoCodes.roomNumber}</dd>
              </div>
              <div>
                <dt>Reservation</dt>
                <dd>{demoCodes.reservationCode}</dd>
              </div>
              <div>
                <dt>Payment reference</dt>
                <dd>{demoCodes.paymentReference}</dd>
              </div>
            </dl>
            <button
              className="secondary-button full-width-button"
              disabled={isBusy}
              onClick={regenerateDemoCodes}
            >
              Regenerate demo codes
            </button>
          </section>

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
                <dd>{currentReservationId ?? "-"}</dd>
              </div>
              <div>
                <dt>Billing account</dt>
                <dd>{currentAccountId ?? "-"}</dd>
              </div>
              <div>
                <dt>Balance</dt>
                <dd>
                  {currentBalance === null
                    ? "-"
                    : formatCurrencyFromCents(
                        currentBalance,
                        currentCurrency,
                      )}
                </dd>
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
                    <span>{event.created_at}</span>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <ResultBlock outcome={lastOutcome} />
        </aside>
      </section>
    </>
  );
}
