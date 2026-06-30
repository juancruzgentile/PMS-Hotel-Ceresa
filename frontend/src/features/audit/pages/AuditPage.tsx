import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  FileSearch,
} from "lucide-react";

import { apiRequest } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { EmptyState } from "@/shared/components/EmptyState";
import { PageHeader } from "@/shared/components/PageHeader";

type JsonRecord = Record<string, unknown>;

type AuditEvent = {
  id: number;
  module: string;
  event_type: string;
  entity_type: string;
  entity_id: number;
  reservation_id: number | null;
  room_id: number | null;
  billing_account_id: number | null;
  actor_user_id: number | null;
  before_state?: JsonRecord;
  after_state?: JsonRecord;
  metadata?: JsonRecord;
  before_state_json?: string | null;
  after_state_json?: string | null;
  metadata_json?: string | null;
  created_at: string;
};

class LocalValidationError extends Error {}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected API error.";
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

function formatJson(value: unknown): string {
  if (value === undefined || value === null) {
    return "{}";
  }

  if (typeof value === "string") {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }

  return JSON.stringify(value, null, 2);
}

function getSearchText(event: AuditEvent): string {
  return [
    event.id,
    event.module,
    event.event_type,
    event.entity_type,
    event.entity_id,
    event.reservation_id,
    event.room_id,
    event.billing_account_id,
    event.actor_user_id,
    event.created_at,
    formatJson(event.before_state ?? event.before_state_json),
    formatJson(event.after_state ?? event.after_state_json),
    formatJson(event.metadata ?? event.metadata_json),
  ]
    .filter((value) => value !== null && value !== undefined)
    .join(" ")
    .toLowerCase();
}

export function AuditPage() {
  const [reservationId, setReservationId] = useState("");
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(
    null,
  );
  const [moduleFilter, setModuleFilter] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [lastOperation, setLastOperation] = useState<string | null>(null);

  async function loadEvents() {
    setIsLoading(true);
    setError(null);

    try {
      const parsedReservationId = parsePositiveInteger(
        reservationId,
        "reservation_id",
      );
      const data = await apiRequest<AuditEvent[]>(
        endpoints.reception.events(parsedReservationId),
      );

      setEvents(data);
      setSelectedEvent(data[0] ?? null);
      setLastMessage(
        `${data.length} audit event(s) loaded for reservation_id ${parsedReservationId}.`,
      );
      setLastOperation("Reservation audit events loaded.");
    } catch (loadError) {
      const prefix =
        loadError instanceof LocalValidationError
          ? "Validation"
          : "API error";
      setError(`${prefix}: ${getErrorMessage(loadError)}`);
    } finally {
      setIsLoading(false);
    }
  }

  const moduleOptions = useMemo(
    () => Array.from(new Set(events.map((event) => event.module))).sort(),
    [events],
  );

  const eventTypeOptions = useMemo(
    () =>
      Array.from(new Set(events.map((event) => event.event_type))).sort(),
    [events],
  );

  const filteredEvents = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return events.filter((event) => {
      const matchesModule =
        moduleFilter === "" || event.module === moduleFilter;
      const matchesEventType =
        eventTypeFilter === "" || event.event_type === eventTypeFilter;
      const matchesSearch =
        normalizedSearch === "" ||
        getSearchText(event).includes(normalizedSearch);

      return matchesModule && matchesEventType && matchesSearch;
    });
  }, [events, moduleFilter, eventTypeFilter, searchTerm]);

  const actorEventCount = events.filter(
    (event) => event.actor_user_id !== null,
  ).length;
  const billingEventCount = events.filter(
    (event) => event.billing_account_id !== null,
  ).length;

  return (
    <>
      <PageHeader
        title="Audit"
        description="Inspect immutable reception audit events by reservation."
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
            <ClipboardList size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Loaded events</p>
            <strong className="metric-value">{events.length}</strong>
            <p className="metric-detail">For current reservation</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <FileSearch size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Visible events</p>
            <strong className="metric-value">{filteredEvents.length}</strong>
            <p className="metric-detail">After frontend filters</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <CheckCircle2 size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">With actor</p>
            <strong className="metric-value">{actorEventCount}</strong>
            <p className="metric-detail">Manual traceability only</p>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-card-icon">
            <AlertTriangle size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="metric-label">Billing linked</p>
            <strong className="metric-value">{billingEventCount}</strong>
            <p className="metric-detail">Events with account ID</p>
          </div>
        </article>
      </section>

      <section className="audit-layout">
        <div className="content-panel">
          <div className="panel-heading">
            <div>
              <h2>Reservation events</h2>
              <p>
                The current backend exposes audit events by reservation_id
                through Reception.
              </p>
            </div>
            <button
              className="secondary-button"
              disabled={isLoading || reservationId.trim() === ""}
              onClick={() => void loadEvents()}
            >
              Load events
            </button>
          </div>

          <div className="audit-toolbar">
            <label>
              reservation_id
              <input
                type="number"
                min="1"
                placeholder="Example: 1"
                value={reservationId}
                onChange={(event) => setReservationId(event.target.value)}
              />
            </label>
            <label>
              Module
              <select
                value={moduleFilter}
                onChange={(event) => setModuleFilter(event.target.value)}
              >
                <option value="">All modules</option>
                {moduleOptions.map((moduleName) => (
                  <option key={moduleName} value={moduleName}>
                    {moduleName}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Event type
              <select
                value={eventTypeFilter}
                onChange={(event) =>
                  setEventTypeFilter(event.target.value)
                }
              >
                <option value="">All event types</option>
                {eventTypeOptions.map((eventType) => (
                  <option key={eventType} value={eventType}>
                    {eventType}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Search
              <input
                placeholder="IDs, actor, type or state text"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </label>
          </div>

          {isLoading ? (
            <p className="muted-text">Loading audit events...</p>
          ) : events.length === 0 ? (
            <EmptyState
              title="No audit events loaded"
              message="Enter a reservation_id from Reception or Reservations, then load events."
            />
          ) : filteredEvents.length === 0 ? (
            <EmptyState
              title="No matching events"
              message="Adjust the module, event type or search filters."
            />
          ) : (
            <div className="audit-table">
              <div className="audit-table-row audit-table-head">
                <span>event_id</span>
                <span>Module</span>
                <span>Event type</span>
                <span>Entity</span>
                <span>Reservation</span>
                <span>Room</span>
                <span>Billing</span>
                <span>Actor</span>
                <span>Created</span>
              </div>
              {filteredEvents.map((event) => (
                <button
                  className={`audit-table-row ${
                    selectedEvent?.id === event.id ? "selected" : ""
                  }`}
                  key={event.id}
                  onClick={() => {
                    setSelectedEvent(event);
                    setLastOperation(`Audit event ${event.id} selected.`);
                  }}
                >
                  <span>{event.id}</span>
                  <span>{event.module}</span>
                  <span>{event.event_type}</span>
                  <span>
                    {event.entity_type} #{event.entity_id}
                  </span>
                  <span>{event.reservation_id ?? "-"}</span>
                  <span>{event.room_id ?? "-"}</span>
                  <span>{event.billing_account_id ?? "-"}</span>
                  <span>{event.actor_user_id ?? "-"}</span>
                  <span>{event.created_at}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <aside className="audit-detail">
          <section className="content-panel mvp-summary">
            <h2>Event detail</h2>
            {selectedEvent ? (
              <>
                <div className="warning-banner">
                  Audit trail is internal traceability. actor_user_id is not
                  real authentication.
                </div>
                <dl>
                  <div>
                    <dt>event_id</dt>
                    <dd>{selectedEvent.id}</dd>
                  </div>
                  <div>
                    <dt>Module</dt>
                    <dd>{selectedEvent.module}</dd>
                  </div>
                  <div>
                    <dt>Event type</dt>
                    <dd>{selectedEvent.event_type}</dd>
                  </div>
                  <div>
                    <dt>Entity</dt>
                    <dd>
                      {selectedEvent.entity_type} #{selectedEvent.entity_id}
                    </dd>
                  </div>
                  <div>
                    <dt>reservation_id</dt>
                    <dd>{selectedEvent.reservation_id ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>room_id</dt>
                    <dd>{selectedEvent.room_id ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>billing_account_id</dt>
                    <dd>{selectedEvent.billing_account_id ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>actor_user_id</dt>
                    <dd>{selectedEvent.actor_user_id ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>Created</dt>
                    <dd>{selectedEvent.created_at}</dd>
                  </div>
                </dl>

                <div className="detail-actions">
                  {selectedEvent.reservation_id ? (
                    <Link className="text-link" to="/reservations">
                      Open Reservations
                    </Link>
                  ) : null}
                  {selectedEvent.room_id ? (
                    <Link className="text-link" to="/rooms">
                      Open Rooms
                    </Link>
                  ) : null}
                </div>

                {selectedEvent.billing_account_id ? (
                  <p className="detail-note">
                    Use billing_account_id{" "}
                    <strong>{selectedEvent.billing_account_id}</strong> in
                    Billing to inspect the account.
                  </p>
                ) : null}
              </>
            ) : (
              <p className="muted-text">
                Select an audit event to inspect immutable details.
              </p>
            )}
          </section>

          {selectedEvent ? (
            <section className="content-panel audit-json-panel">
              <h2>Event state</h2>
              <details open>
                <summary>before_state_json</summary>
                <pre>
                  {formatJson(
                    selectedEvent.before_state ??
                      selectedEvent.before_state_json,
                  )}
                </pre>
              </details>
              <details open>
                <summary>after_state_json</summary>
                <pre>
                  {formatJson(
                    selectedEvent.after_state ??
                      selectedEvent.after_state_json,
                  )}
                </pre>
              </details>
              <details>
                <summary>metadata_json</summary>
                <pre>
                  {formatJson(
                    selectedEvent.metadata ?? selectedEvent.metadata_json,
                  )}
                </pre>
              </details>
            </section>
          ) : null}
        </aside>
      </section>
    </>
  );
}
