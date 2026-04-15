const { Router } = require("express");
const { getHistory, deleteHistory } = require("../controllers/history.controller");
const { requireQuery } = require("../middlewares/validate");

const router = Router();

router.get("/", requireQuery("userId"), getHistory);
router.delete("/", requireQuery("userId"), deleteHistory);

module.exports = router;
