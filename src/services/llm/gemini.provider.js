const axios = require("axios");
const config = require("../../config");
const KeyRotator = require("../../utils/keyRotator");
const logger = require("../../utils/logger");

const BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models";

let rotator = null;

function getRotator() {
  if (!rotator) {
    if (!config.googleApiKeys.length) {
      throw new Error(
        "No Google API keys configured. Set GOOGLE_API_KEY1 (and optionally KEY2, KEY3...) in your .env"
      );
    }
    rotator = new KeyRotator(config.googleApiKeys);
    logger.info("Gemini key rotator ready", { keys: rotator.count, model: config.geminiModel });
  }
  return rotator;
}

async function generate(prompt) {
  const r = getRotator();
  const url = `${BASE_URL}/${config.geminiModel}:generateContent`;

  let lastError;

  for (let attempt = 0; attempt < r.count; attempt++) {
    const apiKey = r.current();

    try {
      const response = await axios.post(
        url,
        {
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.7, maxOutputTokens: 512 },
        },
        {
          params:  { key: apiKey },
          timeout: config.llmTimeout,
        }
      );

      const text = response.data?.candidates?.[0]?.content?.parts?.[0]?.text;
      if (!text) throw new Error("Gemini returned an empty response body");

      r.reset();
      return text.trim();
    } catch (err) {
      lastError = err;
      const status = err.response?.status;

      if (status === 429 || status === 403) {
        logger.warn("Gemini key exhausted — rotating to next", {
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
