import { useCallback, useRef } from "react";

export function useServerClock() {
  const offset = useRef(0);

  const sync = useCallback((serverTime: string) => {
    const parsed = Date.parse(serverTime);
    if (!Number.isNaN(parsed)) {
      offset.current = parsed - Date.now();
    }
  }, []);

  const now = useCallback(() => Date.now() + offset.current, []);

  return { sync, now };
}
