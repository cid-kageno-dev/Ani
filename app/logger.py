import logging
import sys

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"

BRIGHT_RED     = "\033[91m"
BRIGHT_GREEN   = "\033[92m"
BRIGHT_YELLOW  = "\033[93m"
BRIGHT_BLUE    = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN    = "\033[96m"
BRIGHT_WHITE   = "\033[97m"

LEVEL_COLORS = {
    "DEBUG":    DIM + WHITE,
    "INFO":     BRIGHT_CYAN,
    "WARNING":  BRIGHT_YELLOW,
    "ERROR":    BRIGHT_RED,
    "CRITICAL": BOLD + RED,
}

NAME_COLORS = {
    "ani.boot":    BRIGHT_MAGENTA,
    "ani.config":  BLUE,
    "ani.routes":  BRIGHT_GREEN,
    "ani.ai":      BRIGHT_MAGENTA,
    "ani.db":      BRIGHT_BLUE,
    "ani.github":  CYAN,
    "ani.chat":    BRIGHT_WHITE,
}


class AniFormatter(logging.Formatter):
    def format(self, record):
        ts    = self.formatTime(record, "%H:%M:%S")
        level = record.levelname.ljust(8)
        name  = record.name.replace("ani.", "").ljust(8)
        msg   = record.getMessage()

        lc = LEVEL_COLORS.get(record.levelname, WHITE)
        nc = NAME_COLORS.get(record.name, DIM + WHITE)

        ts_str    = f"{DIM}{ts}{RESET}"
        level_str = f"{lc}{BOLD}{level}{RESET}"
        name_str  = f"{nc}[{name.strip()}]{RESET}"
        msg_str   = msg

        if record.levelname in ("ERROR", "CRITICAL"):
            msg_str = f"{BRIGHT_RED}{msg}{RESET}"
        elif record.levelname == "WARNING":
            msg_str = f"{BRIGHT_YELLOW}{msg}{RESET}"

        line = f"{ts_str}  {level_str}  {name_str}  {msg_str}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)

        return line


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(AniFormatter())
        logger.addHandler(handler)
    logger.propagate = False
    return logger


def setup_logging(level: str = "INFO"):
    numeric = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric)

    for name in list(logging.root.manager.loggerDict.keys()):
        if name.startswith("ani."):
            logging.getLogger(name).setLevel(numeric)

    werkzeug_log = logging.getLogger("werkzeug")
    werkzeug_log.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(AniFormatter())
    werkzeug_log.addHandler(handler)
    werkzeug_log.propagate = False
    werkzeug_log.setLevel(logging.INFO)


def divider(char: str = "─", width: int = 52):
    print(f"{DIM}{char * width}{RESET}", flush=True)


def log_box(lines: list[str], color: str = BRIGHT_CYAN, width: int = 52):
    border = f"{color}{BOLD}{'═' * width}{RESET}"
    print(border, flush=True)
    for line in lines:
        padded = line.ljust(width - 2)
        print(f"{color}{BOLD}║{RESET} {padded} {color}{BOLD}║{RESET}", flush=True)
    print(border, flush=True)


def log_status(label: str, ok: bool, detail: str = ""):
    icon  = f"{BRIGHT_GREEN}✓{RESET}" if ok else f"{BRIGHT_RED}✗{RESET}"
    label_str = f"{BRIGHT_WHITE}{label:<18}{RESET}"
    detail_str = f"{DIM}{detail}{RESET}" if detail else ""
    print(f"  {icon}  {label_str}  {detail_str}", flush=True)
