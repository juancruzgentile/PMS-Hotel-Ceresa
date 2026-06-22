export function formatCurrencyFromCents(
  amountCents: number,
  currency = "EUR",
): string {
  return new Intl.NumberFormat("en", {
    style: "currency",
    currency,
  }).format(amountCents / 100);
}
