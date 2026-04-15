require("dotenv").config();

function loadGoogleApiKeys() {
  const keys = [];
  let i = 1;
  while (true) {
    const key = process.env[`GOOGLE_API_KEY${i}`];
    if (!key) break;
    keys.push(key);
    i++;
  }
  if (keys.length === 0 && process.env.GOOGLE_API_KEY) {
    keys.push(process.env.GOOGLE_API_KEY);
  }
  return keys;
}

module.exports = {
  port:             parseInt(process.env.PORT, 10) || 3000,

  llmProvider:      process.env.LLM_PROVIDER || "ollama",
  useFallback:      process.env.USE_FALLBACK === "true",

  ollamaUrl:        process.env.OLLAMA_URL || "http://localhost:11434",
  ollamaModel:      process.env.MODEL_NAME || "mistral",

  geminiModel:      process.env.GEMINI_MODEL || "gemini-2.0-flash",
  googleApiKeys:    loadGoogleApiKeys(),

  openaiApiKey:     process.env.OPENAI_API_KEY || "",
  openaiModel:      process.env.OPENAI_MODEL || "gpt-3.5-turbo",

  memoryLimit:      parseInt(process.env.MEMORY_LIMIT, 10) || 20,
  llmTimeout:       parseInt(process.env.LLM_TIMEOUT, 10) || 30000,

  rateLimitWindow:  parseInt(process.env.RATE_LIMIT_WINDOW, 10) || 60000,
  rateLimitMax:     parseInt(process.env.RATE_LIMIT_MAX, 10) || 30,

  defaultPersonality:
    "Ani is an intelligent, calm, slightly playful anime-style AI companion.",
};
