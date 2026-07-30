import { useEffect, useRef, useState } from "react";
import { randomEvent } from "@/lib/mock-data";
import type { ToolCallEvent, LiveFeedTotals } from "@/types";

const FEED_INTERVAL_MS = 1400;
const CLOCK_INTERVAL_MS = 1000;
const MAX_VISIBLE_EVENTS = 8;

/**
 * Drives the live traffic table + block feed.
 *
 * This currently simulates events client-side so the UI is demoable without a
 * backend running. To wire it to the real WAF, replace the setInterval body
 * with a poll against `${API_BASE_URL}/logs?since=${lastTs}` and map the
 * response into ToolCallEvent[].
 */
export function useLiveFeed() {
  const [events, setEvents] = useState<ToolCallEvent[]>(() => [randomEvent()]);
  const [totals, setTotals] = useState<LiveFeedTotals>({ total: 1, blocked: 0 });
  const [now, setNow] = useState(Date.now());

  useEffect(() => {

    const fetchLogs = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/logs?limit=50");
        if (res.ok) {
          const data = await res.json();
          const fetchedLogs = data.logs || [];
          
          let t = 0;
          let b = 0;
          const mappedEvents: ToolCallEvent[] = fetchedLogs.map((log: any) => {
            t++;
            if (log.disposition === "block") b++;
            
            let ruleKey = null;
            if (log.rule_results) {
              const failedRule = log.rule_results.find((r: any) => !r.allowed && !r.shadow);
              if (failedRule) ruleKey = failedRule.rule_type;
            }
            
            return {
              id: log.log_id,
              agent: log.agent_id,
              tool: log.tool,
              disposition: log.disposition,
              rule: ruleKey,
              ts: log.timestamp * 1000
            };
          });
          
          setEvents(mappedEvents.slice(0, MAX_VISIBLE_EVENTS));
          setTotals({ total: t, blocked: b });
        }
      } catch (err) {
        console.error("Failed to fetch WAF logs:", err);
      }
    };

    const feedInterval = setInterval(fetchLogs, FEED_INTERVAL_MS);
    fetchLogs(); // initial fetch

    const clockInterval = setInterval(() => setNow(Date.now()), CLOCK_INTERVAL_MS);

    return () => {
      clearInterval(feedInterval);
      clearInterval(clockInterval);
    };
  }, []);

  const blockRate = totals.total ? Math.round((totals.blocked / totals.total) * 100) : 0;
  const blockedFeed = events.filter((e) => e.disposition === "block").slice(0, 5);

  return { events, totals, now, blockRate, blockedFeed };
}
