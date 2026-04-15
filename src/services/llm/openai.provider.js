const axios = require("axios");
const config = require("../../config");
const KeyRotator = require("../../utils/keyRotator");
const logger = require("../../utils/logger");

const BASE_URL = "https://api.openai.com/v1/chat/completions";

let rotator = null;

function getRotator() {
  if (!rotator) {
    if (!config.openaiApiKeys.length) {
      throw new Error(
        "No OpenAI API keys configured. Set OPENAI_API_KEY1 (or OPENAI_API_KEY) in your .env"
      );
    }
    rotator = new KeyRotator(config.openaiApiKeys);
    logger.info("OpenAI key rotator ready", { keys: rotator.count, model: config.openaiModel });
  }
  return rotator;
}

async function generate(prompt) {
  const r = getRotator();

  let lastError;

  for (let attempt = 0; attempt < r.count; attempt++) {
    const apiKey = r.current();

    try {
      const response = await axios.post(
        BASE_URL,
        {
          model:       config.openaiModel,
          messages:    [{ role: "user", content: prompt }],
          temperature: 0.7,
        },
        {
          timeout: config.llmTimeout,
          headers: {
            Authorization:  `Bearer ${apiKey}`,
            "Content-Type": "application/json",
          },
        }
      );

      const text = response.data?.choices?.[0]?.message?.content;
      if (!text) throw new Error("OpenAI returned an empty response body");

      r.reset();
      return text.trim();
    } catch (err) {
      lastError = err;
      const status = err.response?.status;

      if (status === 429 || status === 403) {
        logger.warn("OpenAI key exhausted — rotating to next", {
          attempt: attempt + 1,
          of: r.count,
          status,
        });
        r.rotate();
        continue;
      }

      throw err;
    }
  }

  throw lastError;
}

module.exports = { generate };
