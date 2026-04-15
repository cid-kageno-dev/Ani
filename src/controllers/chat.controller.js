const llm = require("../services/llm");
const memory = require("../services/memory/memory.local");
const personaService = require("../services/persona/persona.service");
const { buildPrompt } = require("../utils/promptBuilder");
const logger = require("../utils/logger");

async function chat(req, res, next) {
  try {
    const { userId, message } = req.body;

    const history = await memory.get(userId);
    const personality = personaService.get(userId);
    const prompt = buildPrompt(personality, history, message);

    logger.info("Sending prompt to LLM", { userId, model: process.env.MODEL_NAME });

    const responseText = await llm.generate(prompt);

    await memory.append(userId, { role: "user", content: message });
    await memory.append(userId, { role: "assistant", content: responseText });

    res.json({ success: true, data: { response: responseText } });
  } catch (err) {
    next(err);
  }
}

module.exports = { chat };
