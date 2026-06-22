import { PageHeader } from "@/shared/components/PageHeader";

export function BillingPage() {
  return (
    <>
      <PageHeader
        title="Billing"
        description="Guest accounts, charges, payments and balances."
      />
      <section className="content-panel">Billing content</section>
    </>
  );
}
