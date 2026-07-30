export type RuleKey = "rate_limit" | "param_blocklist" | "data_scope" | "sequence";

export type Disposition = "allow" | "block";

export interface ToolCallEvent {
  id: string | number;
  agent: string;
  tool: string;
  disposition: Disposition;
  rule: RuleKey | null;
  ts: number;
}

export interface RuleMeta {
  key: RuleKey;
  label: string;
  description: string;
  color: string;
}

export interface PipelineStage {
  title: string;
  sub: string;
}

export interface LiveFeedTotals {
  total: number;
  blocked: number;
}
