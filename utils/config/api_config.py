import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_CONFIG_PATH = PROJECT_ROOT / "config" / "api_config.py"

spec = importlib.util.spec_from_file_location("real_api_config", str(API_CONFIG_PATH))
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

for attr in dir(_mod):
    if not attr.startswith("__"):
        globals()[attr] = getattr(_mod, attr)
