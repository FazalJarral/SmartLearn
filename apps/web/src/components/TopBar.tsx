import { Link } from "react-router-dom";

import { useAuth } from "../lib/auth";
import { initialsFor } from "../lib/initials";
import { Logo } from "./Logo";

export function TopBar({ active }: { active: "Library" | "Upload" }) {
  const { user, signOut } = useAuth();
  const displayName = (user?.user_metadata?.display_name as string | undefined) || user?.email || "";

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-paper-raised">
      <nav
        className="mx-auto flex max-w-[1120px] flex-wrap items-center justify-between gap-3 px-[28px] py-[15px]"
        aria-label="Primary"
      >
        <Link to="/" aria-label="SmartLearn home">
          <Logo />
        </Link>
        <div className="flex flex-wrap items-center gap-[18px]">
          <Link
            to="/"
            className={`text-sm ${active === "Library" ? "font-semibold text-ink" : "font-normal text-muted hover:text-ink"}`}
          >
            Library
          </Link>
          <Link
            to="/upload"
            className={`text-sm ${active === "Upload" ? "font-semibold text-ink" : "font-normal text-muted hover:text-ink"}`}
          >
            Upload
          </Link>
          {user ? (
            <button
              type="button"
              onClick={signOut}
              className="flex h-[30px] w-[30px] items-center justify-center rounded-full bg-ink text-[12px] font-semibold text-paper-raised"
              title="Sign out"
              aria-label="Sign out"
            >
              {initialsFor(displayName)}
            </button>
          ) : (
            <Link
              to="/login"
              className="rounded-[11px] bg-ink px-[14px] py-[9px] text-[13px] font-semibold text-paper-raised transition-colors hover:bg-rust"
            >
              Sign in
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}
