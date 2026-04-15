const llm = require("../services/llm");
const memory = require("../services/memory/memory.local");
const personaService = require("../services/persona/persona.service");
const { buildPrompt } = require("../utils/promptBuilder");
const logger = require("../utils/logger");
const config = require("../config");

async function chat(req, res, next) {
  try {
    const { userId, message } = req.body;

    const [history, personality] = await Promise.all([
      memory.get(userId),
      Promise.resolve(personaService.get(userId)),
    ]);

    const prompt = buildPrompt(personality, history, message);

    logger.info("LLM request", { userId, provider: config.llmProvider });

    const response = await llm.generate(prompt);

    await Promise.all([
      memory.append(userId, { role: "user",      content: message  }),
      memory.append(userId, { role: "assistant", content: response }),
    ]);

    res.json({ success: true, data: { response } });
  } catch (err) {
    next(err);
  }
}

module.exports = { chat };
