import { Link, Route, Routes } from "react-router-dom";

import SearchPage from "./pages/Search";
import PlayerPage from "./pages/Player";

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-ink-800/60 bg-ink-950/60 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link
            to="/"
            className="text-sm font-semibold tracking-wide text-accent-300 transition-colors hover:text-accent-200"
          >
            LLMP
          </Link>
          <span className="text-xs text-slate-500">Russian · v0.1</span>
        </div>
      </header>

      <main className="flex flex-1 flex-col">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/song/:songId" element={<PlayerPage />} />
        </Routes>
      </main>
    </div>
  );
}
