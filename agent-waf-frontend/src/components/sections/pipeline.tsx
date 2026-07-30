import { Terminal, Cloud, ShieldCheck, Server, Database, type LucideIcon } from "lucide-react";
import { SpotlightCard } from "@/components/shared/spotlight-card";
import { useCursorHover } from "@/hooks/use-cursor";
import { PIPELINE } from "@/lib/mock-data";

const ICONS: LucideIcon[] = [Terminal, Cloud, ShieldCheck, Server, Database];

export function Pipeline() {
  const stageHover = useCursorHover("stage");

  return (
    <section id="pipeline" className="px-8 py-20">
      <h2 className="font-display text-2xl font-semibold">How a call gets inspected</h2>
      <p className="mb-8 mt-1 text-sm text-waf-text-muted">
        Five stages between an agent's decision and a tool actually running.
      </p>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
        {PIPELINE.map((stage, i) => {
          const Icon = ICONS[i];
          return (
            <SpotlightCard key={stage.title} className="p-5">
              <div {...stageHover}>
                <p className="font-mono text-xs text-waf-text-muted">0{i + 1}</p>
                <Icon size={22} className="mt-4 text-waf-teal" />
                <p className="mt-4 font-display text-sm font-semibold">{stage.title}</p>
                <p className="mt-1 text-xs text-waf-text-secondary">{stage.sub}</p>
              </div>
            </SpotlightCard>
          );
        })}
      </div>
    </section>
  );
}
