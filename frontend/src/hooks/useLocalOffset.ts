import { useCallback, useEffect, useState } from "react";

const KEY = "llmp.localOffset";

/**
 * Per-song offset stored in localStorage. When present it overrides
 * the community offset on load, so the user's manual sync sticks
 * across reloads regardless of what others have submitted.
 */
export function useLocalOffset(songId: number | undefined) {
  const storageKey = songId != null ? `${KEY}.${songId}` : null;

  const [offsetMs, setOffsetMs] = useState<number>(0);
  const [hasOverride, setHasOverride] = useState<boolean>(false);

  useEffect(() => {
    if (!storageKey) return;
    const raw = localStorage.getItem(storageKey);
    if (raw !== null) {
      const n = Number(raw);
      if (Number.isFinite(n)) {
        setOffsetMs(n);
        setHasOverride(true);
        return;
      }
    }
    setHasOverride(false);
  }, [storageKey]);

  const update = useCallback(
    (ms: number) => {
      setOffsetMs(ms);
      if (storageKey) {
        localStorage.setItem(storageKey, String(ms));
        setHasOverride(true);
      }
    },
    [storageKey],
  );

  const clear = useCallback(() => {
    if (storageKey) localStorage.removeItem(storageKey);
    setHasOverride(false);
    setOffsetMs(0);
  }, [storageKey]);

  return { offsetMs, setOffsetMs: update, hasOverride, clear };
}
