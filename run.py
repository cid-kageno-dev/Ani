from app import create_app
from app.logger import get_logger

log = get_logger("ani.boot")
app = create_app()

if __name__ == "__main__":
    log.info("Starting dev server on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
