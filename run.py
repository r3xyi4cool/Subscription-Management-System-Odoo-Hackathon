import os
import sys

# Ensure current directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Auto-fallback to virtualenv python if packages are in venv
venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
if os.path.exists(venv_python) and sys.executable != venv_python:
    try:
        import flask
    except ImportError:
        os.execv(venv_python, [venv_python] + sys.argv)

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=False)

