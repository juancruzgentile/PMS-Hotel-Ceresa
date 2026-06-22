import { PageHeader } from "@/shared/components/PageHeader";

export function RoomsPage() {
  return (
    <>
      <PageHeader
        title="Rooms"
        description="Room availability, cleaning and maintenance status."
      />
      <section className="content-panel">Rooms content</section>
    </>
  );
}
