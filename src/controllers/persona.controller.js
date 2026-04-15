const personaService = require("../services/persona/persona.service");

async function setPersona(req, res, next) {
  try {
    const { userId, personality } = req.body;

    personaService.set(userId, personality);

    res.json({
      success: true,
      data: { userId, personality: personaService.get(userId) },
    });
  } catch (err) {
    next(err);
  }
}

module.exports = { setPersona };
