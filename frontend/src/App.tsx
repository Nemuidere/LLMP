import { Link, NavLink, Route, Routes } from "react-router-dom";

import SearchPage from "./pages/Search";
import PlayerPage from "./pages/Player";
import LibraryPage from "./pages/Library";

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
          <nav className="flex items-center gap-5 text-xs">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `transition-colors ${isActive ? "text-accent-200" : "text-slate-400 hover:text-slate-100"}`
              }
            >
              Search
            </NavLink>
            <NavLink
              to="/library"
              className={({ isActive }) =>
                `transition-colors ${isActive ? "text-accent-200" : "text-slate-400 hover:text-slate-100"}`
              }
            >
              Library
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="flex flex-1 flex-col">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/library" element={<LibraryPage />} />
          <Route path="/song/:songId" element={<PlayerPage />} />
        </Routes>
      </main>
    </div>
  );
}
