import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

export interface PlayerHandle {
  play: () => void;
  pause: () => void;
  seekMs: (ms: number) => void;
  getCurrentTimeMs: () => number;
}

interface Props {
  videoId: string | null;
}

// Load the IFrame API exactly once.
let apiPromise: Promise<typeof YT> | null = null;
function loadYouTubeApi(): Promise<typeof YT> {
  if (apiPromise) return apiPromise;
  apiPromise = new Promise((resolve) => {
    if (window.YT && window.YT.Player) {
      resolve(window.YT);
      return;
    }
    const tag = document.createElement("script");
    tag.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(tag);
    const prev = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      prev?.();
      resolve(window.YT);
    };
  });
  return apiPromise;
}

const YouTubePlayer = forwardRef<PlayerHandle, Props>(({ videoId }, ref) => {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const playerRef = useRef<YT.Player | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!videoId || !hostRef.current) return;

    loadYouTubeApi().then((YT) => {
      if (cancelled || !hostRef.current) return;
      playerRef.current = new YT.Player(hostRef.current, {
        videoId,
        playerVars: { controls: 1, rel: 0, modestbranding: 1, playsinline: 1 },
        events: {
          onReady: () => setReady(true),
        },
      });
    });

    return () => {
      cancelled = true;
      playerRef.current?.destroy();
      playerRef.current = null;
    };
  }, [videoId]);

  useImperativeHandle(
    ref,
    () => ({
      play: () => playerRef.current?.playVideo(),
      pause: () => playerRef.current?.pauseVideo(),
      seekMs: (ms: number) => playerRef.current?.seekTo(ms / 1000, true),
      getCurrentTimeMs: () => {
        const p = playerRef.current;
        if (!p || !ready) return 0;
        return (p.getCurrentTime?.() ?? 0) * 1000;
      },
    }),
    [ready],
  );

  if (!videoId) {
    return (
      <div className="rounded-xl border border-ink-800 bg-ink-900/60 p-6 text-sm text-slate-400">
        No YouTube video resolved for this song.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-ink-800 bg-black shadow-lg shadow-black/40">
      <div className="aspect-video w-full">
        <div ref={hostRef} className="h-full w-full" />
      </div>
    </div>
  );
});

YouTubePlayer.displayName = "YouTubePlayer";
export default YouTubePlayer;
