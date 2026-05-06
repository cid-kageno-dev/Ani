import sys
import warnings

# Suppress the python-dotenv parse warning from Replit's .env file
warnings.filterwarnings("ignore", message=".*could not parse.*", category=SyntaxWarning)

class _SuppressFilter:
    _SUPPRESS = ("could not parse statement",)

    def __init__(self, stream):
        self._s = stream

    def write(self, text):
        if not any(s in text for s in self._SUPPRESS):
            self._s.write(text)

    def flush(self):
        self._s.flush()

    def __getattr__(self, name):
        return getattr(self._s, name)

sys.stdout = _SuppressFilter(sys.stdout)
sys.stderr = _SuppressFilter(sys.stderr)

from app import create_app
from app.logger import get_logger

log = get_logger("ani.boot")
app = create_app()

if __name__ == "__main__":
    log.info("Starting dev server on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
