/**
 * Round-robin API key rotator with per-request failure tracking.
 * On a rate-limit or auth error, the current key is marked exhausted
 * and the next available key is returned. Once all keys have been
 * tried, the exhaustion set is cleared for the next request cycle.
 */
class KeyRotator {
  constructor(keys = []) {
    if (!Array.isArray(keys) || keys.length === 0) {
      throw new Error("KeyRotator requires at least one key");
    }
    this._keys = [...keys];
    this._index = 0;
    this._exhausted = new Set();
  }

  get count() {
    return this._keys.length;
  }

  current() {
    return this._keys[this._index];
  }

  rotate() {
    this._exhausted.add(this._index);

    const next = this._keys.findIndex((_, i) => !this._exhausted.has(i));
    if (next === -1) {
      this._exhausted.clear();
      this._index = (this._index + 1) % this._keys.length;
    } else {
      this._index = next;
    }

    return this._keys[this._index];
  }

  reset() {
    this._exhausted.clear();
  }
}

module.exports = KeyRotator;
