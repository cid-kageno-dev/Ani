const config = require("../../config");

class PersonaService {
  constructor() {
    this._store = new Map();
  }

  get(userId) {
    return this._store.get(userId) || config.defaultPersonality;
  }

  set(userId, personality) {
    if (!personality || typeof personality !== "string" || !personality.trim()) {
      throw new Error("Personality must be a non-empty string");
    }
    this._store.set(userId, personality.trim());
  }
}

module.exports = new PersonaService();
