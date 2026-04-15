const axios = require("axios");
const config = require("../../config");

async function generate(prompt) {
  const response = await axios.post(
    `${config.ollamaUrl}/api/generate`,
    {
      model:  config.ollamaModel,
      prompt,
      stream: false,
    },
    { timeout: config.llmTimeout }
  );

  const text = response.data?.response;
  if (!text) throw new Error("Ollama returned an empty response body");

  return text.trim();
}

module.exports = { generate };
