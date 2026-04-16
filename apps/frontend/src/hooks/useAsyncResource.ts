import { useCallback, useEffect, useState, type DependencyList } from "react";

export interface AsyncResource<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  reload: () => void;
}

export function useAsyncResource<T>(load: () => Promise<T>, deps: DependencyList): AsyncResource<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    let isActive = true;
    setIsLoading(true);
    setError(null);

    load()
      .then((value) => {
        if (isActive) {
          setData(value);
        }
      })
      .catch((unknownError: unknown) => {
        if (isActive) {
          setError(unknownError instanceof Error ? unknownError : new Error("Unexpected request failure."));
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [...deps, reloadToken]);

  return { data, error, isLoading, reload };
}
