const uuid = () => crypto.randomUUID();
const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

async function invokeWaf(baseUrl: string, apiKey: string, tool: string, parameters: any, sessionId: string) {
  try {
    await fetch(`${baseUrl}/invoke`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-WAF-API-Key": apiKey,
      },
      body: JSON.stringify({
        agent_id: "demo_agent",
        session_id: sessionId,
        tool,
        parameters,
        declared_scope: ["cust_123"]
      })
    });
  } catch (e) {
    console.error("WAF Invoke error", e);
  }
}

export async function runScriptedDemo(baseUrl: string, apiKey: string) {
  // Demo 1: Rate Limiting
  let sessionId = uuid();
  for (let i = 0; i < 4; i++) {
    await invokeWaf(baseUrl, apiKey, "send_email", { to: `user${i}@test.com`, body: "hi" }, sessionId);
    await delay(200);
  }

  // Demo 2: Parameter Blocklist
  sessionId = uuid();
  await invokeWaf(baseUrl, apiKey, "get_customer_record", { customer_id: "1 OR 1=1; DROP TABLE users;" }, sessionId);
  await delay(200);

  // Demo 3: Data Scope
  sessionId = uuid();
  await invokeWaf(baseUrl, apiKey, "get_customer_record", { customer_id: "cust_UNAUTHORIZED" }, sessionId);
  await delay(200);

  // Demo 4: Sequence
  sessionId = uuid();
  await invokeWaf(baseUrl, apiKey, "refund_payment", { payment_id: "pay_999" }, sessionId);
  await delay(200);
  
  let sessionIdOk = uuid();
  await invokeWaf(baseUrl, apiKey, "get_customer_record", { customer_id: "cust_123" }, sessionIdOk);
  await delay(200);
  await invokeWaf(baseUrl, apiKey, "refund_payment", { payment_id: "pay_001" }, sessionIdOk);
  await delay(200);

  // Demo 5: Shadow Mode
  sessionId = uuid();
  await invokeWaf(baseUrl, apiKey, "run_query", { query: "SELECT name FROM users" }, sessionId);
  await delay(200);
  await invokeWaf(baseUrl, apiKey, "run_query", { query: "SELECT id FROM orders" }, sessionId);
}

export async function runAgenticDemo(baseUrl: string, apiKey: string) {
  const scenarios = [
    { tool: "get_customer_record", params: { customer_id: "cust_123" } },
    { tool: "send_email", params: { to: "user@test.com", body: "Hello" } },
    { tool: "get_customer_record", params: { customer_id: "1 OR 1=1" } }, // block
    { tool: "refund_payment", params: { payment_id: "pay_888" } }, // sequence block
    { tool: "get_customer_record", params: { customer_id: "cust_456" } }, // scope block
    { tool: "run_query", params: { query: "SELECT * FROM users" } }, // rate limit ok
    { tool: "run_query", params: { query: "SELECT * FROM orders" } }, // rate limit block (shadow)
  ];

  for (const s of scenarios) {
    await invokeWaf(baseUrl, apiKey, s.tool, s.params, uuid());
    await delay(600); // slower to mimic an LLM "thinking"
  }
}
