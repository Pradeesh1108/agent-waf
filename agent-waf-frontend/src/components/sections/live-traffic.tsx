import { ScanLine, CircleDot, Play, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RULE_MAP, timeAgo } from "@/lib/mock-data";
import type { ToolCallEvent } from "@/types";
import { useState } from "react";
import { runScriptedDemo, runAgenticDemo } from "@/lib/demo-runner";

interface LiveTrafficProps {
  events: ToolCallEvent[];
  blockedFeed: ToolCallEvent[];
  now: number;
}

export function LiveTraffic({ events, blockedFeed, now }: LiveTrafficProps) {
  const [isRunningScripted, setIsRunningScripted] = useState(false);
  const [isRunningAgentic, setIsRunningAgentic] = useState(false);

  const handleRunScripted = async () => {
    setIsRunningScripted(true);
    const apiKey = import.meta.env.VITE_WAF_API_KEY || "super-secret-key";
    const baseUrl = import.meta.env.VITE_WAF_URL || "https://yq2kv5vkf6.execute-api.us-east-1.amazonaws.com";
    await runScriptedDemo(baseUrl, apiKey);
    setIsRunningScripted(false);
  };

  const handleRunAgentic = async () => {
    setIsRunningAgentic(true);
    const apiKey = import.meta.env.VITE_WAF_API_KEY || "super-secret-key";
    const baseUrl = import.meta.env.VITE_WAF_URL || "https://yq2kv5vkf6.execute-api.us-east-1.amazonaws.com";
    await runAgenticDemo(baseUrl, apiKey);
    setIsRunningAgentic(false);
  };

  return (
    <section id="live-traffic" className="border-t border-waf-border px-4 md:px-8 py-20">
      <div className="mb-1 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span
            className="inline-block h-2 w-2 rounded-full bg-waf-teal"
            style={{ animation: "waf-pulse 1.6s ease-in-out infinite" }}
          />
          <h2 className="font-display text-2xl font-semibold">Live traffic</h2>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button 
            variant="outline" 
            size="sm" 
            className="text-xs" 
            onClick={handleRunScripted}
            disabled={isRunningScripted || isRunningAgentic}
          >
            {isRunningScripted ? <Loader2 size={12} className="mr-2 animate-spin" /> : <Play size={12} className="mr-2" />}
            Run Scripted Demo
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            className="text-xs" 
            onClick={handleRunAgentic}
            disabled={isRunningScripted || isRunningAgentic}
          >
            {isRunningAgentic ? <Loader2 size={12} className="mr-2 animate-spin" /> : <Play size={12} className="mr-2" />}
            Run Agentic Demo
          </Button>
        </div>
      </div>
      <p className="mb-8 mt-1 text-sm text-waf-text-muted">
        Simulated feed — every call is logged with agent, tool, rule outcome, and disposition.
      </p>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <TrafficTable events={events} now={now} />
        <BlockFeed events={blockedFeed} now={now} />
      </div>
    </section>
  );
}

function TrafficTable({ events, now }: { events: ToolCallEvent[]; now: number }) {
  return (
    <div className="overflow-x-auto min-w-0 rounded-xl border border-waf-border bg-waf-surface lg:col-span-2">
      <div className="min-w-[600px]">
        <div className="grid grid-cols-4 border-b border-waf-border px-5 py-3 text-xs uppercase tracking-wide text-waf-text-muted">
          <span>Agent</span>
          <span>Tool</span>
          <span>Rule</span>
          <span className="text-right">Disposition</span>
        </div>
        {events.map((e) => (
          <div
            key={e.id}
            className="grid grid-cols-4 items-center border-b border-waf-border/60 px-5 py-3 font-mono text-xs last:border-b-0"
          >
            <span className="text-waf-text-secondary truncate pr-2">{e.agent}</span>
            <span className="truncate pr-2">{e.tool}</span>
            <span style={{ color: e.rule ? RULE_MAP[e.rule].color : "var(--color-waf-text-muted)" }}>
              {e.rule ? RULE_MAP[e.rule].label : "—"}
            </span>
            <span className="text-right">
              <Badge variant={e.disposition === "block" ? "block" : "default"}>
                {e.disposition} · {timeAgo(e.ts, now)}
              </Badge>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function BlockFeed({ events, now }: { events: ToolCallEvent[]; now: number }) {
  return (
    <div className="rounded-xl border border-waf-border bg-waf-surface p-5">
      <p className="mb-4 flex items-center gap-2 font-display text-sm font-semibold">
        <ScanLine size={14} className="text-waf-coral" /> Block feed
      </p>
      {events.length === 0 && (
        <p className="text-xs text-waf-text-muted">No blocks yet — clean run.</p>
      )}
      {events.map((e) => (
        <div key={e.id} className="mb-3 border-b border-waf-border/60 pb-3 last:mb-0 last:border-b-0">
          <div className="flex items-center gap-2 font-mono text-xs text-waf-coral">
            <CircleDot size={10} /> {e.tool}
          </div>
          <p className="mt-1 text-xs text-waf-text-secondary">
            {e.agent} · {e.rule ? RULE_MAP[e.rule].label : "—"} · {timeAgo(e.ts, now)}
          </p>
        </div>
      ))}
    </div>
  );
}
