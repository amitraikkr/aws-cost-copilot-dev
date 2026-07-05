const test = require("node:test");
const assert = require("node:assert/strict");

const {
  buildSlackSignature,
  getHeader,
  verifySlackRequest,
} = require("../../shared/src/slack-signature");

test("getHeader reads headers case-insensitively", () => {
  const headers = {
    "X-Slack-Signature": "abc",
  };

  assert.equal(getHeader(headers, "x-slack-signature"), "abc");
});

test("verifySlackRequest accepts a valid Slack signature", () => {
  const signingSecret = "secret";
  const timestamp = "12345";
  const rawBody = "command=%2Fcost&text=help";
  const signature = buildSlackSignature(signingSecret, timestamp, rawBody);

  const result = verifySlackRequest({
    signingSecret,
    rawBody,
    nowSeconds: 12346,
    headers: {
      "x-slack-request-timestamp": timestamp,
      "x-slack-signature": signature,
    },
  });

  assert.deepEqual(result, { ok: true });
});

test("verifySlackRequest rejects stale timestamps", () => {
  const signingSecret = "secret";
  const timestamp = "10000";
  const rawBody = "command=%2Fcost&text=help";
  const signature = buildSlackSignature(signingSecret, timestamp, rawBody);

  const result = verifySlackRequest({
    signingSecret,
    rawBody,
    nowSeconds: 20000,
    headers: {
      "x-slack-request-timestamp": timestamp,
      "x-slack-signature": signature,
    },
  });

  assert.deepEqual(result, { ok: false, reason: "stale_timestamp" });
});

test("verifySlackRequest rejects mismatched signatures", () => {
  const result = verifySlackRequest({
    signingSecret: "secret",
    rawBody: "command=%2Fcost&text=help",
    nowSeconds: 12346,
    headers: {
      "x-slack-request-timestamp": "12345",
      "x-slack-signature": "v0=bad",
    },
  });

  assert.deepEqual(result, { ok: false, reason: "signature_mismatch" });
});
