require("dotenv").config();
const app = require("./app");
const config = require("./config");
const logger = require("./utils/logger");

const server = app.listen(config.port, "0.0.0.0", () => {
  logger.info(`Ani backend running on port ${config.port}`, {
    model: config.modelName,
    ollama: config.ollamaUrl,
    fallback: config.useFallback,
  });
});

process.on("unhandledRejection", (reason) => {
  logger.error("Unhandled promise rejection", reason);
  server.close(() => process.exit(1));
});

process.on("SIGTERM", () => {
  logger.info("SIGTERM received — shutting down gracefully");
  server.close(() => process.exit(0));
});
