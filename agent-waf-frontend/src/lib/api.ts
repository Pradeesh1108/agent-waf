import type { ToolCallEvent } from "@/types";

/**
 * Base URL of the deployed Agent WAF API (API Gateway stage URL from the SAM
 * deploy output). Falls back to localhost for `sam local start-api`.
 */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:3000";

interface RawLogRecord {
  log_id: string;
  agent_id: string;
  tool: string;
  disposition: "allow" | "block";
  rule_results: { rule_type: string; passed: boolean; shadow: boolean }[];
  ts_epoch: number;
}

function mapRecord(r: RawLogRecord, index: number): ToolCallEvent {
  const failedRule = r.rule_results.find((rr) => !rr.passed && !rr.shadow);
  return {
    id: index,
    agent: r.agent_id,
    tool: r.tool,
    disposition: r.disposition,
    rule: (failedRule?.rule_type as ToolCallEvent["rule"]) ?? null,
    ts: r.ts_epoch * 1000,
  };
}

/**
 * Polls the real backend's GET /logs endpoint. Swap `useLiveFeed`'s simulated
 * interval for this once the WAF is deployed:
 *
 *   const records = await fetchRecentLogs(lastSeenTs);
 */
export async function fetchRecentLogs(sinceEpochSeconds = 0, limit = 20): Promise<ToolCallEvent[]> {
  const res = await fetch(`${API_BASE_URL}/logs?since=${sinceEpochSeconds}&limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch logs: ${res.status}`);
  const data: RawLogRecord[] = await res.json();
  return data.map(mapRecord);
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
