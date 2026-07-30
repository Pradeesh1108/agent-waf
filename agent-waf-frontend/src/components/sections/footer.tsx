import { TECH_STACK } from "@/lib/mock-data";

export function Footer() {
  return (
    <footer className="flex flex-wrap items-center gap-3 border-t border-waf-border px-4 md:px-8 py-10">
      {TECH_STACK.map((t) => (
        <span
          key={t}
          className="rounded-full border border-waf-border-strong px-3 py-1 font-mono text-xs text-waf-text-muted"
        >
          {t}
        </span>
      ))}
    </footer>
  );
}
