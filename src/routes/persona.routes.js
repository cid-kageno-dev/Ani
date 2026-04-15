const { Router } = require("express");
const { setPersona } = require("../controllers/persona.controller");
const { requireBody } = require("../middlewares/validate");

const router = Router();

router.post("/", requireBody("userId", "personality"), setPersona);

module.exports = router;
