const test = require("node:test");
const assert = require("node:assert/strict");

const {
  helpText,
  plainTextBlock,
  unknownCommandText,
} = require("../../shared/src/slack-format");

test("helpText lists supported commands", () => {
  const text = helpText();

  assert.match(text, /AWS Cost Copilot commands:/);
  assert.match(text, /\/cost today/);
  assert.match(text, /\/cost service EC2/);
});

test("unknownCommandText includes invalid input and help", () => {
  const text = unknownCommandText("forecast");

  assert.match(text, /forecast/);
  assert.match(text, /\/cost help/);
});

test("plainTextBlock builds a Slack mrkdwn section", () => {
  assert.deepEqual(plainTextBlock("hello"), {
    type: "section",
    text: {
      type: "mrkdwn",
      text: "hello",
    },
  });
});
