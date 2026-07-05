const SUPPORTED_COMMANDS = [
  "/cost help",
  "/cost today",
  "/cost yesterday",
  "/cost month",
  "/cost last 7 days",
  "/cost service",
  "/cost service EC2",
];

function parseSlackFormBody(rawBody) {
  const params = new URLSearchParams(rawBody || "");
  return Object.fromEntries(params.entries());
}

function normalizeCommandText(text) {
  return String(text || "").trim().replace(/\s+/g, " ").toLowerCase();
}

function parseCostCommand(text) {
  const normalized = normalizeCommandText(text);

  if (!normalized || normalized === "help") {
    return { type: "help" };
  }

  if (normalized === "today") {
    return { type: "cost_summary", range: "today" };
  }

  if (normalized === "yesterday") {
    return { type: "cost_summary", range: "yesterday" };
  }

  if (normalized === "month" || normalized === "this month") {
    return { type: "cost_summary", range: "month" };
  }

  if (normalized === "last 7 days" || normalized === "week") {
    return { type: "cost_summary", range: "last_7_days" };
  }

  if (normalized === "service" || normalized === "services") {
    return { type: "service_breakdown", range: "month", service: null };
  }

  if (normalized.startsWith("service ")) {
    const service = String(text || "").trim().replace(/\s+/g, " ").slice("service ".length).trim();
    if (service) {
      return { type: "service_breakdown", range: "month", service };
    }
  }

  return {
    type: "unknown",
    input: String(text || "").trim(),
    supportedCommands: SUPPORTED_COMMANDS,
  };
}

module.exports = {
  SUPPORTED_COMMANDS,
  normalizeCommandText,
  parseCostCommand,
  parseSlackFormBody,
};
