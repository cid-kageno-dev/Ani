const { MemoryInterface } = require("./memory.interface");
const config = require("../../config");

class LocalMemory extends MemoryInterface {
  constructor() {
    super();
    this._store = new Map();
  }

  async get(userId) {
    return this._store.get(userId) || [];
  }

  async append(userId, message) {
    const history = this._store.get(userId) || [];
    history.push(message);
    if (history.length > config.memoryLimit) {
      history.splice(0, history.length - config.memoryLimit);
    }
    this._store.set(userId, history);
  }

  async clear(userId) {
    this._store.delete(userId);
  }
}

module.exports = new LocalMemory();
