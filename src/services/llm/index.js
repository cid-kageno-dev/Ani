const ollama = require("./ollama.provider");
const openai = require("./openai.provider");
const config = require("../../config");
const logger = require("../../utils/logger");

async function generate(prompt) {
  try {
    return await ollama.generate(prompt);
  } catch (err) {
    logger.error("Ollama provider failed", err);

    if (config.useFallback) {
      logger.warn("Falling back to OpenAI provider");
      return await openai.generate(prompt);
    }

    throw err;
  }
}

module.exports = { generate };
