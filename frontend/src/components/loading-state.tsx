export function LoadingState({ title = "Loading data" }: { title?: string }) {
  return (
    <section className="panel state-panel">
      <h2>{title}</h2>
      <p className="muted">Fetching the latest case and review context.</p>
    </section>
  );
}
