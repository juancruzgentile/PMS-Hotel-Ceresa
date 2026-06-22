import { PageHeader } from "@/shared/components/PageHeader";

export function ReservationsPage() {
  return (
    <>
      <PageHeader
        title="Reservations"
        description="Booking calendar, assignments and reservation status."
      />
      <section className="content-panel">Reservations content</section>
    </>
  );
}
