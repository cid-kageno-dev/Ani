import logging
import os

# Suppress verbose dotenv parse warnings before any other imports.
logging.getLogger("dotenv.main").setLevel(logging.ERROR)

from app import create_app          # noqa: E402
from app.logger import get_logger   # noqa: E402

log = get_logger("ani.boot")
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    log.info(f"Starting dev server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
