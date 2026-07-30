import type { RuleMeta, PipelineStage, ToolCallEvent, RuleKey } from "@/types";

export const TOOLS = ["get_customer_record", "send_email", "run_query", "refund_payment"];

export const AGENTS = ["agent-07", "agent-12", "agent-21"];

export const RULES: RuleMeta[] = [
  {
    key: "rate_limit",
    label: "Rate limit",
    description: "Agent may call a tool no more than N times per rolling window.",
    color: "var(--color-waf-indigo)",
  },
  {
    key: "param_blocklist",
    label: "Param blocklist",
    description: "Rejects calls whose parameters match a blocklist or exceed size limits.",
    color: "var(--color-waf-coral)",
  },
  {
    key: "data_scope",
    label: "Data scope",
    description: "Rejects calls that reference data outside the agent's declared scope.",
    color: "var(--color-waf-teal)",
  },
  {
    key: "sequence",
    label: "Sequence",
    description: "Rejects a tool call unless a required prior tool ran in this session.",
    color: "var(--color-waf-amber)",
  },
];

export const RULE_MAP: Record<RuleKey, RuleMeta> = RULES.reduce(
  (acc, r) => ({ ...acc, [r.key]: r }),
  {} as Record<RuleKey, RuleMeta>
);

export const PIPELINE: PipelineStage[] = [
  { title: "Sample agent", sub: "LLM decides which tool to call" },
  { title: "API Gateway", sub: "Public HTTPS entry point" },
  { title: "WAF proxy", sub: "Lambda running the rule engine" },
  { title: "Tool registry", sub: "Executes only allowed calls" },
  { title: "DynamoDB", sub: "State, counters, audit log" },
];

export const TECH_STACK = ["FastAPI", "AWS Lambda", "API Gateway", "DynamoDB", "Claude API", "AWS SAM"];

let idCounter = 0;

/**
 * Generates a single simulated tool-call event, shaped like a record the real
 * /logs endpoint would return. Swap this out for a fetch() to the deployed
 * WAF's /logs?since=<ts> endpoint once the backend is live.
 */
export function randomEvent(): ToolCallEvent {
  const blocked = Math.random() < 0.3;
  const ruleKeys = RULES.map((r) => r.key);
  return {
    id: idCounter++,
    tool: TOOLS[Math.floor(Math.random() * TOOLS.length)],
    agent: AGENTS[Math.floor(Math.random() * AGENTS.length)],
    disposition: blocked ? "block" : "allow",
    rule: blocked ? ruleKeys[Math.floor(Math.random() * ruleKeys.length)] : null,
    ts: Date.now(),
  };
}

export function timeAgo(ts: number, now: number): string {
  const d = new Date(ts);
  const hh = d.getHours().toString().padStart(2, '0');
  const mm = d.getMinutes().toString().padStart(2, '0');
  const ss = d.getSeconds().toString().padStart(2, '0');
  const ms = d.getMilliseconds().toString().padStart(3, '0');
  return `${hh}:${mm}:${ss}.${ms}`;
}
