import { useState } from "react";
import { Link } from "react-router-dom";

import { apiRequest } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { EmptyState } from "@/shared/components/EmptyState";
import { PageHeader } from "@/shared/components/PageHeader";
import { formatCurrencyFromCents } from "@/shared/utils/formatters";

type BillingCharge = {
  id: number;
  source_module: string;
  description: string;
  amount_cents: number;
  created_at: string;
};

type BillingPayment = {
  id: number;
  payment_method: string;
  amount_cents: number;
  reference: string | null;
  created_at: string;
};

type BillingAccount = {
  id: number;
  reservation_id: number;
  reservation_code: string;
  guest_id: number;
  guest_code: string;
  guest_first_name: string;
  guest_last_name: string;
  room_id: number;
  room_number: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  currency: string;
  charges: BillingCharge[];
  payments: BillingPayment[];
  charges_total_cents: number;
  payments_total_cents: number;
  balance_cents: number;
};

type ChargeForm = {
  source_module: string;
  description: string;
  amount_cents: string;
};

type PaymentForm = {
  payment_method: string;
  amount_cents: string;
  reference: string;
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

function optionalText(value: string): string | null {
  const trimmed = value.trim();

  return trimmed === "" ? null : trimmed;
}

function getGuestFullName(account: BillingAccount): string {
  return `${account.guest_first_name} ${account.guest_last_name}`;
}

function getBalanceState(account: BillingAccount): {
  className: string;
  label: string;
} {
  if (account.balance_cents > 0) {
    return {
      className: "warning-banner",
      label: "Open balance. Payment is still pending.",
    };
  }

  if (account.balance_cents === 0) {
    return {
      className: "success-banner",
      label: "Balance is settled.",
    };
  }

  return {
    className: "warning-banner",
    label: "Payments exceed charges. Review this account.",
  };
}

export function BillingPage() {
  const [accountId, setAccountId] = useState("");
  const [account, setAccount] = useState<BillingAccount | null>(null);
  const [chargeForm, setChargeForm] = useState<ChargeForm>({
    source_module: "rooms",
    description: "Accommodation",
    amount_cents: "",
  });
  const [paymentForm, setPaymentForm] = useState<PaymentForm>({
    payment_method: "card",
    amount_cents: "",
    reference: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [lastOperation, setLastOperation] = useState<string | null>(null);

  async function loadAccount(nextAccountId = accountId) {
    setIsLoading(true);
    setError(null);

    try {
      const parsedAccountId = parsePositiveInteger(
        nextAccountId,
        "billing_account_id",
      );
      const data = await apiRequest<BillingAccount>(
        endpoints.billing.account(parsedAccountId),
      );

      setAccount(data);
      setAccountId(String(data.id));
      setLastMessage(`Billing account ${data.id} loaded.`);
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

  async function addCharge() {
    setIsMutating(true);
    setError(null);

    try {
      const parsedAccountId = parsePositiveInteger(
        accountId,
        "billing_account_id",
      );
      const amountCents = parsePositiveInteger(
        chargeForm.amount_cents,
        "Charge amount",
      );

      await apiRequest(endpoints.billing.charges(parsedAccountId), {
        method: "POST",
        body: {
          source_module: chargeForm.source_module,
          description: chargeForm.description,
          amount_cents: amountCents,
        },
      });

      await loadAccount(String(parsedAccountId));
      setLastOperation(
        `Charge added for ${formatCurrencyFromCents(
          amountCents,
          account?.currency,
        )}.`,
      );
      setChargeForm({
        ...chargeForm,
        amount_cents: "",
      });
    } catch (chargeError) {
      const prefix =
        chargeError instanceof LocalValidationError
          ? "Validation"
          : "API error";
      setError(`${prefix}: ${getErrorMessage(chargeError)}`);
    } finally {
      setIsMutating(false);
    }
  }

  async function addPayment() {
    setIsMutating(true);
    setError(null);

    try {
      const parsedAccountId = parsePositiveInteger(
        accountId,
        "billing_account_id",
      );
      const amountCents = parsePositiveInteger(
        paymentForm.amount_cents,
        "Payment amount",
      );

      await apiRequest(endpoints.billing.payments(parsedAccountId), {
        method: "POST",
        body: {
          payment_method: paymentForm.payment_method,
          amount_cents: amountCents,
          reference: optionalText(paymentForm.reference),
        },
      });

      await loadAccount(String(parsedAccountId));
      setLastOperation(
        `Payment registered for ${formatCurrencyFromCents(
          amountCents,
          account?.currency,
        )}.`,
      );
      setPaymentForm({
        ...paymentForm,
        amount_cents: "",
        reference: "",
      });
    } catch (paymentError) {
      const prefix =
        paymentError instanceof LocalValidationError
          ? "Validation"
          : "API error";
      setError(`${prefix}: ${getErrorMessage(paymentError)}`);
    } finally {
      setIsMutating(false);
    }
  }

  const balanceState = account ? getBalanceState(account) : null;
  const accountIsOpen = account?.status === "open";
  const busy = isLoading || isMutating;

  return (
    <>
      <PageHeader
        title="Billing"
        description="Inspect billing accounts, charges, payments and operational balances."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {lastMessage ? (
        <div className="success-banner">{lastMessage}</div>
      ) : null}
      {lastOperation ? (
        <div className="success-banner">{lastOperation}</div>
      ) : null}

      <section className="billing-layout">
        <div className="billing-main">
          <section className="content-panel">
            <div className="panel-heading">
              <div>
                <h2>Account lookup</h2>
                <p>
                  Load an existing account by billing_account_id. A list
                  endpoint is not available yet.
                </p>
              </div>
              <button
                className="secondary-button"
                disabled={busy || accountId.trim() === ""}
                onClick={() => void loadAccount()}
              >
                Load account
              </button>
            </div>

            <div className="billing-toolbar">
              <label>
                Billing account ID
                <input
                  type="number"
                  min="1"
                  placeholder="Example: 1"
                  value={accountId}
                  onChange={(event) => setAccountId(event.target.value)}
                />
              </label>
            </div>

            {isLoading ? (
              <p className="muted-text">Loading billing account...</p>
            ) : account ? (
              <>
                <div className="billing-metrics">
                  <div className="metric-card">
                    <div>
                      <p className="metric-label">Charges</p>
                      <strong className="metric-value">
                        {formatCurrencyFromCents(
                          account.charges_total_cents,
                          account.currency,
                        )}
                      </strong>
                      <p className="metric-detail">
                        {account.charges.length} charge(s)
                      </p>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div>
                      <p className="metric-label">Payments</p>
                      <strong className="metric-value">
                        {formatCurrencyFromCents(
                          account.payments_total_cents,
                          account.currency,
                        )}
                      </strong>
                      <p className="metric-detail">
                        {account.payments.length} payment(s)
                      </p>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div>
                      <p className="metric-label">Balance</p>
                      <strong className="metric-value">
                        {formatCurrencyFromCents(
                          account.balance_cents,
                          account.currency,
                        )}
                      </strong>
                      <p className="metric-detail">{account.status}</p>
                    </div>
                  </div>
                </div>

                {balanceState ? (
                  <div className={balanceState.className}>
                    {balanceState.label}
                  </div>
                ) : null}

                <section className="billing-section">
                  <div className="panel-heading compact">
                    <div>
                      <h2>Charges</h2>
                      <p>Charges posted by hotel modules.</p>
                    </div>
                  </div>

                  {account.charges.length === 0 ? (
                    <EmptyState
                      title="No charges"
                      message="Add a simple operational charge when needed."
                    />
                  ) : (
                    <div className="billing-table">
                      <div className="billing-table-row billing-table-head">
                        <span>ID</span>
                        <span>Source</span>
                        <span>Description</span>
                        <span>Amount</span>
                        <span>Created</span>
                      </div>
                      {account.charges.map((charge) => (
                        <div className="billing-table-row" key={charge.id}>
                          <span>{charge.id}</span>
                          <span>{charge.source_module}</span>
                          <span>{charge.description}</span>
                          <span>
                            {formatCurrencyFromCents(
                              charge.amount_cents,
                              account.currency,
                            )}
                          </span>
                          <span>{charge.created_at}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </section>

                <section className="billing-section">
                  <div className="panel-heading compact">
                    <div>
                      <h2>Payments</h2>
                      <p>
                        Internal payment records only; no bank integration.
                      </p>
                    </div>
                  </div>

                  {account.payments.length === 0 ? (
                    <EmptyState
                      title="No payments"
                      message="Register an internal payment record when the guest pays."
                    />
                  ) : (
                    <div className="billing-table">
                      <div className="billing-table-row billing-table-head">
                        <span>ID</span>
                        <span>Method</span>
                        <span>Reference</span>
                        <span>Amount</span>
                        <span>Created</span>
                      </div>
                      {account.payments.map((payment) => (
                        <div className="billing-table-row" key={payment.id}>
                          <span>{payment.id}</span>
                          <span>{payment.payment_method}</span>
                          <span>{payment.reference ?? "-"}</span>
                          <span>
                            {formatCurrencyFromCents(
                              payment.amount_cents,
                              account.currency,
                            )}
                          </span>
                          <span>{payment.created_at}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              </>
            ) : (
              <EmptyState
                title="No billing account loaded"
                message="Enter a billing_account_id from Reception MVP or a reservation summary, then load the account."
              />
            )}
          </section>
        </div>

        <aside className="billing-detail">
          <section className="content-panel mvp-summary">
            <h2>Account detail</h2>
            {account ? (
              <>
                <dl>
                  <div>
                    <dt>billing_account_id</dt>
                    <dd>{account.id}</dd>
                  </div>
                  <div>
                    <dt>reservation_id</dt>
                    <dd>{account.reservation_id}</dd>
                  </div>
                  <div>
                    <dt>Reservation</dt>
                    <dd>{account.reservation_code}</dd>
                  </div>
                  <div>
                    <dt>Guest</dt>
                    <dd>{getGuestFullName(account)}</dd>
                  </div>
                  <div>
                    <dt>Room</dt>
                    <dd>{account.room_number}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{account.status}</dd>
                  </div>
                  <div>
                    <dt>Currency</dt>
                    <dd>{account.currency}</dd>
                  </div>
                  <div>
                    <dt>Created</dt>
                    <dd>{account.created_at}</dd>
                  </div>
                  <div>
                    <dt>Updated</dt>
                    <dd>{account.updated_at}</dd>
                  </div>
                </dl>

                {account.notes ? (
                  <p className="detail-note">{account.notes}</p>
                ) : null}

                <div className="detail-actions">
                  <Link className="text-link" to="/reservations">
                    Open Reservations
                  </Link>
                  <Link className="text-link" to="/reception-mvp">
                    Open Reception MVP
                  </Link>
                </div>
              </>
            ) : (
              <p className="muted-text">
                Load an account to inspect reservation, guest and balance
                details.
              </p>
            )}
          </section>

          <section className="content-panel mvp-summary">
            <h2>Add charge</h2>
            {account && !accountIsOpen ? (
              <div className="warning-banner">
                This account is not open. The backend will reject new
                movements.
              </div>
            ) : null}
            <div className="form-grid single-column">
              <label>
                Source module
                <select
                  value={chargeForm.source_module}
                  onChange={(event) =>
                    setChargeForm({
                      ...chargeForm,
                      source_module: event.target.value,
                    })
                  }
                >
                  <option value="rooms">rooms</option>
                  <option value="reception">reception</option>
                  <option value="bar">bar</option>
                  <option value="dining_room">dining_room</option>
                  <option value="housekeeping">housekeeping</option>
                  <option value="maintenance">maintenance</option>
                </select>
              </label>
              <label>
                Description
                <input
                  value={chargeForm.description}
                  onChange={(event) =>
                    setChargeForm({
                      ...chargeForm,
                      description: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                amount_cents
                <input
                  type="number"
                  min="1"
                  value={chargeForm.amount_cents}
                  onChange={(event) =>
                    setChargeForm({
                      ...chargeForm,
                      amount_cents: event.target.value,
                    })
                  }
                />
              </label>
            </div>
            <button
              className="primary-button full-width-button"
              disabled={busy || !account || !accountIsOpen}
              onClick={() => void addCharge()}
            >
              Add charge
            </button>
          </section>

          <section className="content-panel mvp-summary">
            <h2>Register payment</h2>
            <p>
              Payments here are internal records; this is not bank or card
              processing.
            </p>
            <div className="form-grid single-column">
              <label>
                Method
                <select
                  value={paymentForm.payment_method}
                  onChange={(event) =>
                    setPaymentForm({
                      ...paymentForm,
                      payment_method: event.target.value,
                    })
                  }
                >
                  <option value="card">card</option>
                  <option value="cash">cash</option>
                  <option value="transfer">transfer</option>
                </select>
              </label>
              <label>
                amount_cents
                <input
                  type="number"
                  min="1"
                  value={paymentForm.amount_cents}
                  onChange={(event) =>
                    setPaymentForm({
                      ...paymentForm,
                      amount_cents: event.target.value,
                    })
                  }
                />
              </label>
              <label>
                Reference
                <input
                  value={paymentForm.reference}
                  onChange={(event) =>
                    setPaymentForm({
                      ...paymentForm,
                      reference: event.target.value,
                    })
                  }
                />
              </label>
            </div>
            <button
              className="primary-button full-width-button"
              disabled={busy || !account || !accountIsOpen}
              onClick={() => void addPayment()}
            >
              Register payment
            </button>
          </section>
        </aside>
      </section>
    </>
  );
}
