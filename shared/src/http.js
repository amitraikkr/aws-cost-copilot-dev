function response(statusCode, body, headers = {}) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: JSON.stringify(body),
  };
}

function textResponse(statusCode, body, headers = {}) {
  return {
    statusCode,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      ...headers,
    },
    body,
  };
}

function ok(body) {
  return response(200, body);
}

function badRequest(message = "Bad request") {
  return response(400, { error: message });
}

function unauthorized() {
  return response(401, { error: "Unauthorized" });
}

function slackMessage(text, options = {}) {
  return response(200, {
    response_type: options.responseType || "ephemeral",
    text,
    ...(options.blocks ? { blocks: options.blocks } : {}),
  });
}

module.exports = {
  badRequest,
  ok,
  response,
  slackMessage,
  textResponse,
  unauthorized,
};
