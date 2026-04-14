export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <section className="panel state-panel">
      <h2>{title}</h2>
      <p className="muted">{detail}</p>
    </section>
  );
}
