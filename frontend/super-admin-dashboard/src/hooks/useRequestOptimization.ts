import { useCallback, useRef } from 'react';

/**
 * Debounced function hook for API calls
 * Prevents excessive API calls during rapid user interactions
 */
export function useDebounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  const timeoutRef = useRef<NodeJS.Timeout>();

  const debouncedFunc = useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        func(...args);
      }, delay);
    },
    [func, delay]
  ) as T;

  return debouncedFunc;
}

/**
 * Throttled function hook for API calls
 * Ensures function is called at most once per specified interval
 */
export function useThrottle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  const lastCallRef = useRef<number>(0);

  const throttledFunc = useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();
      if (now - lastCallRef.current >= delay) {
        lastCallRef.current = now;
        return func(...args);
      }
    },
    [func, delay]
  ) as T;

  return throttledFunc;
}

/**
 * API request batcher
 * Batches multiple API requests into single calls
 */
class RequestBatcher {
  private batches: Map<string, {
    requests: Array<{
      resolve: (value: any) => void;
      reject: (error: any) => void;
      params: any;
    }>;
    timeout: NodeJS.Timeout;
  }> = new Map();

  private batchDelay = 50; // 50ms batch window

  async batch<T>(
    key: string,
    params: any,
    batchFunction: (batchedParams: any[]) => Promise<T[]>
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      let batch = this.batches.get(key);
      
      if (!batch) {
        batch = {
          requests: [],
          timeout: setTimeout(() => this.executeBatch(key, batchFunction), this.batchDelay)
        };
        this.batches.set(key, batch);
      }

      batch.requests.push({ resolve, reject, params });
    });
  }

  private async executeBatch<T>(
    key: string,
    batchFunction: (batchedParams: any[]) => Promise<T[]>
  ) {
    const batch = this.batches.get(key);
    if (!batch) return;

    this.batches.delete(key);

    try {
      const batchedParams = batch.requests.map(req => req.params);
      const results = await batchFunction(batchedParams);
      
      batch.requests.forEach((request, index) => {
        request.resolve(results[index]);
      });
    } catch (error) {
      batch.requests.forEach(request => {
        request.reject(error);
      });
    }
  }
}

export const requestBatcher = new RequestBatcher();

/**
 * Hook for batched API requests
 */
export function useBatchedRequest<T>(
  key: string,
  batchFunction: (params: any[]) => Promise<T[]>
) {
  return useCallback(
    (params: any) => requestBatcher.batch(key, params, batchFunction),
    [key, batchFunction]
  );
}

/**
 * Request deduplication helper
 * Prevents duplicate requests with same parameters
 */
class RequestDeduplicator {
  private ongoing: Map<string, Promise<any>> = new Map();

  async dedupe<T>(key: string, requestFunction: () => Promise<T>): Promise<T> {
    if (this.ongoing.has(key)) {
      return this.ongoing.get(key);
    }

    const promise = requestFunction()
      .finally(() => {
        this.ongoing.delete(key);
      });

    this.ongoing.set(key, promise);
    return promise;
  }
}

export const requestDeduplicator = new RequestDeduplicator();

/**
 * Hook for deduplicated API requests
 */
export function useDedupedRequest<T>(requestFunction: () => Promise<T>) {
  return useCallback(
    (key: string) => requestDeduplicator.dedupe(key, requestFunction),
    [requestFunction]
  );
}
