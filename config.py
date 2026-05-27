import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR = BASE_DIR / "static"
DB_PATH = DATA_DIR / "gestao.db"

PORT = int(os.environ.get("PORT", 18090))
SESSION_SECRET = os.environ.get("SESSION_SECRET", "bbdi-gestao-dev-secret-change-me")
DIRETOR_SENHA = os.environ.get("DIRETOR_SENHA", "trocar-me-diretor")
SUPERVISOR_SENHA_DEFAULT = os.environ.get("SUPERVISOR_SENHA_DEFAULT", "trocar-me-123")
