import { useState } from "react";
import { Gauge, Ban, Eye, ListOrdered, type LucideIcon } from "lucide-react";
import { SpotlightCard } from "@/components/shared/spotlight-card";
import { Switch } from "@/components/ui/switch";
import { useCursorHover } from "@/hooks/use-cursor";
import { RULES } from "@/lib/mock-data";
import type { RuleKey } from "@/types";

const RULE_ICONS: Record<RuleKey, LucideIcon> = {
  rate_limit: Gauge,
  param_blocklist: Ban,
  data_scope: Eye,
  sequence: ListOrdered,
};

const DEFAULT_SHADOW_STATE: Record<RuleKey, boolean> = {
  rate_limit: false,
  param_blocklist: false,
  data_scope: false,
  sequence: true,
};

export function RuleEngine() {
  const [shadowMode, setShadowMode] = useState(DEFAULT_SHADOW_STATE);
  const ruleHover = useCursorHover("rule");
  const toggleHover = useCursorHover("toggle");

  return (
    <section id="rule-engine" className="border-t border-waf-border px-8 py-20">
      <h2 className="font-display text-2xl font-semibold">Rule engine</h2>
      <p className="mb-8 mt-1 text-sm text-waf-text-muted">
        Each rule runs independently in enforce or shadow mode.
      </p>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {RULES.map((rule) => {
          const Icon = RULE_ICONS[rule.key];
          const isShadow = shadowMode[rule.key];
          return (
            <SpotlightCard key={rule.key} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3" {...ruleHover}>
                  <div
                    className="rounded-lg p-2"
                    style={{ background: `color-mix(in srgb, ${rule.color} 15%, transparent)` }}
                  >
                    <Icon size={18} style={{ color: rule.color }} />
                  </div>
                  <div>
                    <p className="font-display text-sm font-semibold">{rule.label}</p>
                    <p className="mt-0.5 font-mono text-xs text-waf-text-muted">{rule.key}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2" {...toggleHover}>
                  <span
                    className="text-xs"
                    style={{ color: isShadow ? "var(--color-waf-amber)" : "var(--color-waf-teal)" }}
                  >
                    {isShadow ? "Shadow" : "Enforce"}
                  </span>
                  <Switch
                    checked={isShadow}
                    onCheckedChange={(checked) =>
                      setShadowMode((prev) => ({ ...prev, [rule.key]: checked }))
                    }
                  />
                </div>
              </div>
              <p className="mt-4 text-xs text-waf-text-secondary">{rule.description}</p>
            </SpotlightCard>
          );
        })}
      </div>
    </section>
  );
}
