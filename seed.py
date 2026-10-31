import sys
import os

# Auto-fallback to virtualenv python if packages are in venv
venv_python = (
    os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")
    if os.name == "nt"
    else os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
)
if os.path.exists(venv_python) and sys.executable != venv_python:
    try:
        import flask
    except ImportError:
        os.execv(venv_python, [venv_python] + sys.argv)

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app import create_app
from backend.seed import run_seed

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run_seed()
