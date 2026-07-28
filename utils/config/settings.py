import sys
from pathlib import Path
import importlib.util

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.py"

spec = importlib.util.spec_from_file_location("real_settings", str(SETTINGS_PATH))
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

for attr in dir(_mod):
    if not attr.startswith("__"):
        globals()[attr] = getattr(_mod, attr)
