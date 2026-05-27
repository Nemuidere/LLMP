// YouTube IFrame API installs this global; declare so TS is happy.
declare global {
  interface Window {
    onYouTubeIframeAPIReady?: () => void;
  }
}

export {};
