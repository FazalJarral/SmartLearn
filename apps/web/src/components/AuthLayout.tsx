import { Link } from "react-router-dom";

import { Logo } from "./Logo";

const chips = ["SUMMARY", "QUIZ", "FLASHCARDS", "VIDEO"];
const proof = ["2.4M pages read", "91% recall at 7 days", "Used in 340 courses"];

type AuthLayoutProps = {
  mode: "signin" | "signup";
  heading: string;
  sub: string;
  children: React.ReactNode;
};

export function AuthLayout({ mode, heading, sub, children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen flex-wrap">
      <div className="relative flex flex-[1_1_480px] flex-col justify-between gap-12 overflow-hidden bg-ink px-6 py-11 text-paper-raised sm:px-12">
        <div
          className="pointer-events-none absolute rounded-full bg-rust opacity-[0.13]"
          style={{ right: -180, top: "46%", width: 420, height: 420, transform: "translateY(-50%)" }}
          aria-hidden="true"
        />
        <div className="relative z-10">
          <Logo tone="paper" />
        </div>
        <div className="relative z-10 max-w-[620px]">
          <p className="mb-6 font-mono text-[11px] uppercase tracking-[0.18em] text-rust-light">
            PDF in · understanding out
          </p>
          <h1 className="font-serif text-[clamp(44px,6vw,88px)] leading-[0.95] tracking-[-0.02em]">
            Read it once.
            <br />
            <em className="text-rust-light not-italic italic">Know it</em> cold.
          </h1>
          <p className="mt-7 max-w-[44ch] text-[17px] leading-[1.6] text-dark-body">
            Drop in a lecture PDF or a paper. Get a summary that cites its own pages, a quiz that finds the gaps,
            cards for the commute, and a two-minute explainer.
          </p>
          <div className="mt-[34px] flex flex-wrap gap-2">
            {chips.map((chip) => (
              <span
                key={chip}
                className="rounded-full border border-ink-line-2 px-[13px] py-2 font-mono text-[11px] tracking-[0.1em] text-dark-chip"
              >
                {chip}
              </span>
            ))}
          </div>
        </div>
        <div className="relative z-10 flex flex-wrap gap-[26px] font-mono text-[12px] text-dark-muted">
          {proof.map((line) => (
            <span key={line}>{line}</span>
          ))}
        </div>
      </div>
      <div className="flex flex-[1_1_400px] items-center justify-center bg-paper-raised px-6 py-12 text-ink sm:px-12">
        <div className="w-full max-w-[372px]">
          <div className="flex rounded-full bg-fill-sunken p-[3px]">
            <Link
              to="/login"
              className={`flex-1 rounded-full px-[14px] py-[7px] text-center text-[13px] transition-colors ${
                mode === "signin" ? "bg-paper-raised font-semibold text-ink shadow-pill" : "font-medium text-muted"
              }`}
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className={`flex-1 rounded-full px-[14px] py-[7px] text-center text-[13px] transition-colors ${
                mode === "signup" ? "bg-paper-raised font-semibold text-ink shadow-pill" : "font-medium text-muted"
              }`}
            >
              Create account
            </Link>
          </div>
          <h2 className="mt-7 font-serif text-[38px] leading-[1.05]">{heading}</h2>
          <p className="mt-2 text-sm text-muted">{sub}</p>
          {children}
          <p className="mt-[26px] text-xs leading-[1.6] text-muted">
            By continuing you agree to the <span className="cursor-default underline">terms</span> and{" "}
            <span className="cursor-default underline">privacy policy</span>.
          </p>
        </div>
      </div>
    </div>
  );
}
