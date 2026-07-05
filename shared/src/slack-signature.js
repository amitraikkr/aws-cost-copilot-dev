const crypto = require("crypto");

const DEFAULT_TOLERANCE_SECONDS = 60 * 5;

function getHeader(headers, name) {
  if (!headers) {
    return undefined;
  }

  const foundKey = Object.keys(headers).find((key) => key.toLowerCase() === name.toLowerCase());
  return foundKey ? headers[foundKey] : undefined;
}

function buildSlackSignature(signingSecret, timestamp, rawBody) {
  const baseString = `v0:${timestamp}:${rawBody || ""}`;
  const digest = crypto
    .createHmac("sha256", signingSecret)
    .update(baseString)
    .digest("hex");

  return `v0=${digest}`;
}

function safeCompare(left, right) {
  const leftBuffer = Buffer.from(left || "", "utf8");
  const rightBuffer = Buffer.from(right || "", "utf8");

  if (leftBuffer.length !== rightBuffer.length) {
    return false;
  }

  return crypto.timingSafeEqual(leftBuffer, rightBuffer);
}

function verifySlackRequest({
  signingSecret,
  headers,
  rawBody,
  nowSeconds = Math.floor(Date.now() / 1000),
  toleranceSeconds = DEFAULT_TOLERANCE_SECONDS,
}) {
  if (!signingSecret) {
    return { ok: false, reason: "missing_signing_secret" };
  }

  const timestamp = getHeader(headers, "x-slack-request-timestamp");
  const signature = getHeader(headers, "x-slack-signature");

  if (!timestamp || !signature) {
    return { ok: false, reason: "missing_slack_headers" };
  }

  const timestampSeconds = Number(timestamp);
  if (!Number.isFinite(timestampSeconds)) {
    return { ok: false, reason: "invalid_timestamp" };
  }

  if (Math.abs(nowSeconds - timestampSeconds) > toleranceSeconds) {
    return { ok: false, reason: "stale_timestamp" };
  }

  const expectedSignature = buildSlackSignature(signingSecret, timestamp, rawBody);
  if (!safeCompare(expectedSignature, signature)) {
    return { ok: false, reason: "signature_mismatch" };
  }

  return { ok: true };
}

module.exports = {
  DEFAULT_TOLERANCE_SECONDS,
  buildSlackSignature,
  getHeader,
  verifySlackRequest,
};
