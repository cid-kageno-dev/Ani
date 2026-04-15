/**
 * Memory interface contract.
 * Any memory implementation must provide these methods.
 *
 * get(userId)             → message[]
 * append(userId, message) → void
 * clear(userId)           → void
 */
class MemoryInterface {
  async get(userId) {
    throw new Error("get() not implemented");
  }

  async append(userId, message) {
    throw new Error("append() not implemented");
  }

  async clear(userId) {
    throw new Error("clear() not implemented");
  }
}

module.exports = { MemoryInterface };
