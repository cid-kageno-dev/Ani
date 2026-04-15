const express = require("express");
const logger = require("./utils/logger");
const rateLimiter = require("./middlewares/rateLimiter");
const errorHandler = require("./middlewares/errorHandler");
const routes = require("./routes");

const app = express();

app.use(express.json());

app.use((req, res, next) => {
  logger.request(req);
  next();
});

app.use(rateLimiter);

app.use("/", routes);

app.use((req, res) => {
  res.status(404).json({ success: false, error: "Route not found" });
});

app.use(errorHandler);

module.exports = app;
