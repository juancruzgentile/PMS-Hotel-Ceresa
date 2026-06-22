import { PageHeader } from "@/shared/components/PageHeader";

export function GuestsPage() {
  return (
    <>
      <PageHeader
        title="Guests"
        description="Guest profiles and stay history."
      />
      <section className="content-panel">Guests content</section>
    </>
  );
}
