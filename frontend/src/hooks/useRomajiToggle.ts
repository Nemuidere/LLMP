import { useCallback, useEffect, useState } from "react";

const KEY = "llmp.showRomaji";

/**
 * Romaji visibility toggle. Default = on for Russian (the
 * transliteration is the main reading aid), off for Japanese (kana
 * reading already sits above the kanji as furigana, romaji is
 * beginner-only).
 */
export function useRomajiToggle(language: string | undefined) {
  const computeDefault = useCallback(() => (language === "ja" ? false : true), [language]);

  const [show, setShow] = useState<boolean>(() => {
    if (typeof window === "undefined") return computeDefault();
    const raw = localStorage.getItem(`${KEY}.${language ?? "default"}`);
    if (raw === "true") return true;
    if (raw === "false") return false;
    return computeDefault();
  });

  useEffect(() => {
    if (language) localStorage.setItem(`${KEY}.${language}`, String(show));
  }, [show, language]);

  // When the language for the currently-loaded song flips, recompute default.
  useEffect(() => {
    const raw = localStorage.getItem(`${KEY}.${language ?? "default"}`);
    if (raw === null) setShow(computeDefault());
  }, [language, computeDefault]);

  return { show, toggle: () => setShow((v) => !v) };
}
