import sys
import os
import importlib.util

# Path to the actual app.py inside the subdirectory
subfolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AI-Personal-Finance-Tracker")
app_py_path = os.path.join(subfolder, "app.py")

# Add the subfolder to sys.path so internal imports (routes, services) resolve correctly
if subfolder not in sys.path:
    sys.path.insert(0, subfolder)

# Load the subdirectory app.py module directly under a unique namespace to avoid name collisions
spec = importlib.util.spec_from_file_location("real_app", app_py_path)
real_app = importlib.util.module_from_spec(spec)
sys.modules["real_app"] = real_app
spec.loader.exec_module(real_app)

# Expose the Flask app instance for Gunicorn (app:app)
app = real_app.app
