import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/shared/stat-card";
import { useCursorHover } from "@/hooks/use-cursor";
import type { LiveFeedTotals } from "@/types";

interface HeroProps {
  totals: LiveFeedTotals;
  blockRate: number;
}

export function Hero({ totals, blockRate }: HeroProps) {
  const primaryCta = useCursorHover("scroll");
  const secondaryCta = useCursorHover("view");

  return (
    <section className="waf-grid-bg relative overflow-hidden px-8 pb-20 pt-24">
      <div
        className="pointer-events-none absolute left-0 right-0 h-24"
        style={{
          background: "linear-gradient(180deg, transparent, rgba(45,212,191,0.06), transparent)",
          animation: "waf-scan 6s linear infinite",
        }}
      />

      <div className="relative max-w-3xl">
        <Badge className="mb-6">Policy-enforcing proxy for agent tool calls</Badge>
        <h1 className="font-display text-5xl font-bold leading-tight md:text-6xl">
          Every tool call.
          <br />
          Inspected, every time.
        </h1>
        <p className="mt-6 max-w-xl text-lg text-waf-text-secondary">
          A WAF was never built for agents. This is the missing inspection layer: rate
          limits, parameter validation, data scope, and call-order enforcement, sitting
          directly between an agent's decision and a tool's execution.
        </p>
        <div className="mt-8 flex gap-4">
          <Button 
            size="lg" 
            {...primaryCta}
            onClick={() => document.getElementById("live-traffic")?.scrollIntoView({ behavior: "smooth" })}
          >
            View live traffic
          </Button>
          <Button 
            size="lg" 
            variant="outline" 
            {...secondaryCta}
            onClick={() => document.getElementById("pipeline")?.scrollIntoView({ behavior: "smooth" })}
          >
            Read the architecture
          </Button>
        </div>
      </div>

      <div className="relative mt-16 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Calls inspected" value={totals.total} />
        <StatCard label="Blocked" value={totals.blocked} accent="var(--color-waf-coral)" />
        <StatCard label="Block rate" value={`${blockRate}%`} accent="var(--color-waf-amber)" />
        <StatCard label="Rules active" value="4" accent="var(--color-waf-teal)" />
      </div>
    </section>
  );
}
