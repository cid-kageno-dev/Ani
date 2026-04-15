const config = require("../../config");
const logger = require("../../utils/logger");

const registry = {
  ollama: () => require("./ollama.provider"),
  gemini: () => require("./gemini.provider"),
  openai: () => require("./openai.provider"),
};

function getProvider(name) {
  const factory = registry[name];
  if (!factory) throw new Error(`Unknown LLM provider: "${name}". Valid options: ${Object.keys(registry).join(", ")}`);
  return factory();
}

async function generate(prompt) {
  const primary = config.llmProvider;

  try {
    return await getProvider(primary).generate(prompt);
  } catch (err) {
    logger.error(`LLM provider "${primary}" failed`, err);

    if (config.useFallback && primary !== "openai") {
      logger.warn(`Falling back to OpenAI`);
      return await getProvider("openai").generate(prompt);
    }

    throw err;
  }
}

module.exports = { generate };
