function timestamp() {
  return new Date().toISOString();
}

function info(message, meta = {}) {
  const extra = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : "";
  console.log(`[${timestamp()}] INFO  ${message}${extra}`);
}

function warn(message, meta = {}) {
  const extra = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : "";
  console.warn(`[${timestamp()}] WARN  ${message}${extra}`);
}

function error(message, err = null) {
  const detail = err ? ` | ${err.message || err}` : "";
  console.error(`[${timestamp()}] ERROR ${message}${detail}`);
}

function request(req) {
  info(`${req.method} ${req.originalUrl}`, { ip: req.ip });
}

module.exports = { info, warn, error, request };
