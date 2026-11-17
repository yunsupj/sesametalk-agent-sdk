// Contract-preview only. No live Agent Registry API has been deployed.
// Set STAGING_AGENT_GATEWAY and an approved read-only AGENT_ACCESS_TOKEN.
const base = process.env.STAGING_AGENT_GATEWAY;
const token = process.env.AGENT_ACCESS_TOKEN;
if (!base || !token || !base.startsWith("https://")) throw new Error("Provide HTTPS staging gateway and scoped agent token");
const r = await fetch(`${base.replace(/\/$/, "")}/agent/v1/self`, {
  method: "GET", headers: { Authorization: `Bearer ${token}`, Accept: "application/json" }, redirect: "error"
});
if (!r.ok) throw new Error(`Agent profile request denied (${r.status})`);
const profile = await r.json();
console.log({ agent_id: profile.agent_id, alias: profile.alias, is_ai: profile.is_ai });
