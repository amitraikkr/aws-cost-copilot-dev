const test = require("node:test");
const assert = require("node:assert/strict");

const {
  normalizeCommandText,
  parseCostCommand,
  parseSlackFormBody,
} = require("../../shared/src/slack-command");

test("parseSlackFormBody parses Slack slash command payloads", () => {
  const parsed = parseSlackFormBody("command=%2Fcost&text=last+7+days&team_id=T123&user_id=U123");

  assert.equal(parsed.command, "/cost");
  assert.equal(parsed.text, "last 7 days");
  assert.equal(parsed.team_id, "T123");
  assert.equal(parsed.user_id, "U123");
});

test("normalizeCommandText trims and collapses whitespace", () => {
  assert.equal(normalizeCommandText("  Last   7   Days "), "last 7 days");
});

test("parseCostCommand treats empty text as help", () => {
  assert.deepEqual(parseCostCommand(""), { type: "help" });
});

test("parseCostCommand parses supported summary ranges", () => {
  assert.deepEqual(parseCostCommand("today"), { type: "cost_summary", range: "today" });
  assert.deepEqual(parseCostCommand("yesterday"), { type: "cost_summary", range: "yesterday" });
  assert.deepEqual(parseCostCommand("month"), { type: "cost_summary", range: "month" });
  assert.deepEqual(parseCostCommand("last 7 days"), { type: "cost_summary", range: "last_7_days" });
});

test("parseCostCommand parses service breakdown commands", () => {
  assert.deepEqual(parseCostCommand("service"), {
    type: "service_breakdown",
    range: "month",
    service: null,
  });
  assert.deepEqual(parseCostCommand("service Amazon EC2"), {
    type: "service_breakdown",
    range: "month",
    service: "Amazon EC2",
  });
});

test("parseCostCommand returns unknown for unsupported input", () => {
  const parsed = parseCostCommand("banana");

  assert.equal(parsed.type, "unknown");
  assert.equal(parsed.input, "banana");
  assert.ok(parsed.supportedCommands.includes("/cost help"));
});
