const { Router } = require("express");
const chatRoutes = require("./chat.routes");
const personaRoutes = require("./persona.routes");
const historyRoutes = require("./history.routes");

const router = Router();

router.use("/chat", chatRoutes);
router.use("/persona", personaRoutes);
router.use("/history", historyRoutes);

router.get("/health", (req, res) => {
  res.json({ success: true, data: { status: "ok", uptime: process.uptime() } });
});

module.exports = router;
