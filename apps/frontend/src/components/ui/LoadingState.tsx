interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "Loading data..." }: LoadingStateProps) {
  return (
    <div className="flex min-h-40 items-center justify-center rounded-2xl border border-dashed border-line bg-white px-6 py-10 text-sm text-slate">
      <div className="flex items-center gap-3">
        <span className="h-3 w-3 animate-pulse rounded-full bg-accent" />
        <span>{label}</span>
      </div>
    </div>
  );
}
