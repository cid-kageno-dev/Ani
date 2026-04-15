require("dotenv").config();
const app = require("./app");
const config = require("./config");
const logger = require("./utils/logger");

const server = app.listen(config.port, "0.0.0.0", () => {
  logger.info("Ani backend started", {
    port:     config.port,
    provider: config.llmProvider,
    model:    config.llmProvider === "gemini"
                ? config.geminiModel
                : config.llmProvider === "openai"
                  ? config.openaiModel
                  : config.ollamaModel,
    keys:     config.googleApiKeys.length || undefined,
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
