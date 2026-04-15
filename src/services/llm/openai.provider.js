const axios = require("axios");
const config = require("../../config");

async function generate(prompt) {
  if (!config.openaiApiKey) {
    throw new Error("OpenAI API key is not configured");
  }

  const response = await axios.post(
    "https://api.openai.com/v1/chat/completions",
    {
      model: "gpt-3.5-turbo",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.7,
    },
    {
      timeout: config.llmTimeout,
      headers: {
        Authorization: `Bearer ${config.openaiApiKey}`,
        "Content-Type": "application/json",
      },
    }
  );

  const text = response.data?.choices?.[0]?.message?.content;
  if (!text) {
    throw new Error("OpenAI returned an empty response");
  }

  return text.trim();
}

module.exports = { generate };
