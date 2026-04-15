const C = {
  reset:  "\x1b[0m",
  dim:    "\x1b[2m",
  bold:   "\x1b[1m",
  green:  "\x1b[32m",
  yellow: "\x1b[33m",
  red:    "\x1b[31m",
  cyan:   "\x1b[36m",
  blue:   "\x1b[34m",
  white:  "\x1b[37m",
};

function c(color, text) {
  return `${C[color]}${text}${C.reset}`;
}

function ts() {
  return c("dim", new Date().toISOString());
}

function meta(obj) {
  if (!obj || !Object.keys(obj).length) return "";
  return " " + c("dim", JSON.stringify(obj));
}

function info(message, data = {}) {
  console.log(`${ts()} ${c("green", "INFO ")} ${message}${meta(data)}`);
}

function warn(message, data = {}) {
  console.warn(`${ts()} ${c("yellow", "WARN ")} ${message}${meta(data)}`);
}

function error(message, err = null) {
  const detail = err ? c("dim", ` | ${err.message || String(err)}`) : "";
  console.error(`${ts()} ${c("red", "ERROR")} ${message}${detail}`);
}

function request(req, res, ms) {
  const method = c("cyan", req.method.padEnd(7));
  const status = res.statusCode;
  const sc = status >= 500 ? "red" : status >= 400 ? "yellow" : "green";
  const duration = c("dim", `${ms}ms`);
  console.log(`${ts()} ${c("blue", "HTTP ")} ${method} ${req.originalUrl} ${c(sc, String(status))} ${duration}`);
}

module.exports = { info, warn, error, request };
