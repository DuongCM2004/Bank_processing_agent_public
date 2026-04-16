import type { PropsWithChildren } from "react";

import { Button } from "@/components/ui/Button";

interface StateBlockProps {
  state: "loading" | "empty" | "error";
  title: string;
  message?: string;
  onRetry?: () => void;
}

export function StateBlock({ state, title, message, onRetry }: StateBlockProps) {
  const toneClassName =
    state === "error"
      ? "border-red/20 bg-redSoft text-red"
      : state === "loading"
        ? "border-blue/20 bg-blueSoft text-blue"
        : "border-line bg-surface text-muted";

  return (
    <div className={`rounded-lg border p-6 ${toneClassName}`} role={state === "error" ? "alert" : "status"}>
      <p className="text-sm font-semibold text-ink">{title}</p>
      {message ? <p className="mt-2 text-sm leading-6">{message}</p> : null}
      {onRetry ? (
        <Button className="mt-4" type="button" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}

interface AsyncBoundaryProps {
  isLoading: boolean;
  error: Error | null;
  isEmpty: boolean;
  emptyTitle: string;
  emptyMessage: string;
  loadingTitle?: string;
  onRetry?: () => void;
}

export function AsyncBoundary({
  isLoading,
  error,
  isEmpty,
  emptyTitle,
  emptyMessage,
  loadingTitle = "Loading data",
  onRetry,
  children,
}: PropsWithChildren<AsyncBoundaryProps>) {
  if (isLoading) {
    return <StateBlock state="loading" title={loadingTitle} message="Requesting current operational data." />;
  }

  if (error) {
    return <StateBlock state="error" title="Unable to load data" message={error.message} onRetry={onRetry} />;
  }

  if (isEmpty) {
    return <StateBlock state="empty" title={emptyTitle} message={emptyMessage} />;
  }

  return <>{children}</>;
}
