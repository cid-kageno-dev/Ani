const config = require("../config");

const hits = new Map();

function rateLimiter(req, res, next) {
  const key = req.ip;
  const now = Date.now();
  const entry = hits.get(key);

  if (!entry || now - entry.start > config.rateLimitWindow) {
    hits.set(key, { start: now, count: 1 });
    return next();
  }

  entry.count += 1;

  if (entry.count > config.rateLimitMax) {
    return res.status(429).json({
      success: false,
      error: "Too many requests. Please slow down.",
    });
  }

  next();
}

module.exports = rateLimiter;
