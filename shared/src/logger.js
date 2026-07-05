const LEVELS = {
  DEBUG: 10,
  INFO: 20,
  WARN: 30,
  ERROR: 40,
};

function createLogger(context = {}) {
  const configuredLevel = (process.env.LOG_LEVEL || "INFO").toUpperCase();
  const minimumLevel = LEVELS[configuredLevel] || LEVELS.INFO;

  function write(level, message, details = {}) {
    if ((LEVELS[level] || LEVELS.INFO) < minimumLevel) {
      return;
    }

    console.log(JSON.stringify({
      level,
      message,
      ...context,
      ...details,
    }));
  }

  return {
    debug: (message, details) => write("DEBUG", message, details),
    info: (message, details) => write("INFO", message, details),
    warn: (message, details) => write("WARN", message, details),
    error: (message, details) => write("ERROR", message, details),
  };
}

module.exports = {
  createLogger,
};
