export type BillingCharge = {
  id: number;
  source_module: string;
  description: string;
  amount_cents: number;
  created_at: string;
};

export type BillingPayment = {
  id: number;
  payment_method: "card" | "cash" | "transfer";
  amount_cents: number;
  reference: string | null;
  created_at: string;
};

export type BillingAccount = {
  id: number;
  reservation_id: number;
  reservation_code: string;
  guest_id: number;
  guest_code: string;
  guest_first_name: string;
  guest_last_name: string;
  room_id: number;
  room_number: string;
  status: "open" | "closed" | "cancelled";
  notes: string | null;
  charges: BillingCharge[];
  payments: BillingPayment[];
  charges_total_cents: number;
  payments_total_cents: number;
  balance_cents: number;
  currency: string;
  created_at: string;
  updated_at: string;
};
