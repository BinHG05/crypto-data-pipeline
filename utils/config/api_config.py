from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_CONFIG_PATH = PROJECT_ROOT / "config" / "api_config.py"

spec = spec_from_file_location("project_api_config", API_CONFIG_PATH)
module = module_from_spec(spec)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load config from {API_CONFIG_PATH}")

spec.loader.exec_module(module)

COINGECKO_API = module.COINGECKO_API
REDDIT_API = module.REDDIT_API
BUCKET_NAME = module.BUCKET_NAME
