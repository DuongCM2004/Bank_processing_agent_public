import type { ReactNode } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";

interface AsyncContentProps {
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyMessage?: string;
  onRetry?: () => void;
  children: ReactNode;
}

export function AsyncContent({
  isLoading,
  isError,
  errorMessage = "The requested data could not be loaded.",
  isEmpty = false,
  emptyTitle = "No data found",
  emptyMessage = "There is no data to show yet.",
  onRetry,
  children,
}: AsyncContentProps) {
  if (isLoading) {
    return <LoadingState />;
  }

  if (isError) {
    return <ErrorState message={errorMessage} onRetry={onRetry} />;
  }

  if (isEmpty) {
    return <EmptyState title={emptyTitle} message={emptyMessage} />;
  }

  return <>{children}</>;
}
