const axios = require("axios");
const config = require("../../config");
const logger = require("../../utils/logger");

async function generate(prompt) {
  const url = `${config.ollamaUrl}/api/generate`;

  const response = await axios.post(
    url,
    {
      model: config.modelName,
      prompt,
      stream: false,
    },
    {
      timeout: config.llmTimeout,
    }
  );

  const text = response.data?.response;
  if (!text) {
    throw new Error("Ollama returned an empty response");
  }

  return text.trim();
}

module.exports = { generate };
