require("dotenv").config();

module.exports = {
  port: parseInt(process.env.PORT, 10) || 3000,
  ollamaUrl: process.env.OLLAMA_URL || "http://localhost:11434",
  modelName: process.env.MODEL_NAME || "mistral",
  useFallback: process.env.USE_FALLBACK === "true",
  openaiApiKey: process.env.OPENAI_API_KEY || "",
  memoryLimit: parseInt(process.env.MEMORY_LIMIT, 10) || 20,
  defaultPersonality:
    "Ani is an intelligent, calm, slightly playful anime-style AI companion.",
  rateLimitWindow: parseInt(process.env.RATE_LIMIT_WINDOW, 10) || 60000,
  rateLimitMax: parseInt(process.env.RATE_LIMIT_MAX, 10) || 30,
  llmTimeout: parseInt(process.env.LLM_TIMEOUT, 10) || 30000,
};
