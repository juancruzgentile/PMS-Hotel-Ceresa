type EmptyStateProps = {
  title: string;
  message?: string;
};

export function EmptyState({ title, message }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      {message ? <p>{message}</p> : null}
    </div>
  );
}
