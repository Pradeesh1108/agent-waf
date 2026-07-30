interface StatCardProps {
  label: string;
  value: string | number;
  accent?: string;
}

export function StatCard({ label, value, accent }: StatCardProps) {
  return (
    <div className="rounded-xl border border-waf-border bg-waf-surface p-5">
      <p className="font-body text-xs uppercase tracking-wide text-waf-text-muted">{label}</p>
      <p
        className="mt-2 font-display text-3xl font-semibold"
        style={{ color: accent ?? "var(--color-waf-text)" }}
      >
        {value}
      </p>
    </div>
  );
}
