const { Router } = require("express");
const { chat } = require("../controllers/chat.controller");
const { requireBody } = require("../middlewares/validate");

const router = Router();

router.post("/", requireBody("userId", "message"), chat);

module.exports = router;
