type LogoProps = {
  tone?: "ink" | "paper";
};

export function Logo({ tone = "ink" }: LogoProps) {
  return (
    <div className="flex items-center gap-[11px]">
      <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-rust text-[13px] font-bold text-white">
        S
      </div>
      <span
        className={`font-sans text-[13px] font-medium uppercase tracking-[0.18em] ${
          tone === "paper" ? "text-paper-raised" : "text-ink"
        }`}
      >
        SmartLearn
      </span>
    </div>
  );
}
