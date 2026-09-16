type PdfGlyphProps = {
  width?: number;
  height?: number;
  radius?: number;
  variant?: "ink" | "paper";
};

export function PdfGlyph({ width = 50, height = 64, radius = 6, variant = "ink" }: PdfGlyphProps) {
  const fill = variant === "ink" ? "bg-ink" : "bg-paper-raised";
  const label = variant === "ink" ? "text-rust-light" : "text-ink";
  return (
    <div
      className={`flex shrink-0 items-end ${fill}`}
      style={{ width, height, borderRadius: radius, padding: 9 }}
      aria-hidden="true"
    >
      <span className={`font-mono text-[10px] ${label}`}>PDF</span>
    </div>
  );
}
