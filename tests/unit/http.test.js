const test = require("node:test");
const assert = require("node:assert/strict");

const {
  badRequest,
  ok,
  slackMessage,
  textResponse,
  unauthorized,
} = require("../../shared/src/http");

test("ok returns a JSON HTTP response", () => {
  assert.deepEqual(ok({ status: "ok" }), {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status: "ok" }),
  });
});

test("textResponse returns plain text", () => {
  assert.deepEqual(textResponse(200, "OK"), {
    statusCode: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
    body: "OK",
  });
});

test("badRequest and unauthorized return stable error shapes", () => {
  assert.equal(badRequest("Invalid").statusCode, 400);
  assert.deepEqual(JSON.parse(badRequest("Invalid").body), { error: "Invalid" });

  assert.equal(unauthorized().statusCode, 401);
  assert.deepEqual(JSON.parse(unauthorized().body), { error: "Unauthorized" });
});

test("slackMessage returns an ephemeral Slack response by default", () => {
  const response = slackMessage("hello");

  assert.equal(response.statusCode, 200);
  assert.deepEqual(JSON.parse(response.body), {
    response_type: "ephemeral",
    text: "hello",
  });
});
