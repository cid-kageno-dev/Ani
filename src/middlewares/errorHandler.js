const logger = require("../utils/logger");

const AXIOS_TIMEOUT_CODES = new Set(["ECONNABORTED", "ETIMEDOUT"]);
const AXIOS_NETWORK_CODES = new Set(["ECONNREFUSED", "ENOTFOUND", "ECONNRESET"]);

function classify(err) {
  if (AXIOS_TIMEOUT_CODES.has(err.code)) {
    return { status: 504, message: "LLM provider timed out" };
  }
  if (AXIOS_NETWORK_CODES.has(err.code)) {
    return { status: 502, message: "Could not reach LLM provider" };
  }
  if (err.response?.status === 429) {
    return { status: 429, message: "LLM provider rate limit reached" };
  }
  return {
    status: err.status || err.response?.status || 500,
    message: err.status !== 500 && err.message ? err.message : "An internal error occurred",
  };
}

function errorHandler(err, req, res, next) {
  const { status, message } = classify(err);
  logger.error(`${req.method} ${req.originalUrl} → ${status}`, err);
  res.status(status).json({ success: false, error: message });
}

module.exports = errorHandler;
