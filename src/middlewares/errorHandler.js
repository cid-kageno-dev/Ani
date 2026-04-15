const logger = require("../utils/logger");

function errorHandler(err, req, res, next) {
  logger.error(`Unhandled error on ${req.method} ${req.originalUrl}`, err);

  const status = err.status || err.response?.status || 500;
  const message =
    status === 500
      ? "An internal error occurred"
      : err.message || "Request failed";

  res.status(status).json({ success: false, error: message });
}

module.exports = errorHandler;
