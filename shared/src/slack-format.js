const { SUPPORTED_COMMANDS } = require("./slack-command");

function helpText() {
  return [
    "AWS Cost Copilot commands:",
    ...SUPPORTED_COMMANDS.map((command) => `- ${command}`),
  ].join("\n");
}

function unknownCommandText(input) {
  const suffix = input ? `: ${input}` : "";
  return `I do not recognize that cost command${suffix}.\n\n${helpText()}`;
}

function plainTextBlock(text) {
  return {
    type: "section",
    text: {
      type: "mrkdwn",
      text,
    },
  };
}

module.exports = {
  helpText,
  plainTextBlock,
  unknownCommandText,
};
