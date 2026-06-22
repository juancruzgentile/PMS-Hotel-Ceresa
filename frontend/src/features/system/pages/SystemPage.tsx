import { PageHeader } from "@/shared/components/PageHeader";

export function SystemPage() {
  return (
    <>
      <PageHeader
        title="System"
        description="Enabled modules and application health."
      />
      <section className="content-panel">System content</section>
    </>
  );
}
