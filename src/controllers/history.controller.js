const memory = require("../services/memory/memory.local");

async function getHistory(req, res, next) {
  try {
    const { userId } = req.query;
    const history = await memory.get(userId);
    res.json({ success: true, data: { userId, history } });
  } catch (err) {
    next(err);
  }
}

async function deleteHistory(req, res, next) {
  try {
    const { userId } = req.query;
    await memory.clear(userId);
    res.json({ success: true, data: { userId, cleared: true } });
  } catch (err) {
    next(err);
  }
}

module.exports = { getHistory, deleteHistory };
