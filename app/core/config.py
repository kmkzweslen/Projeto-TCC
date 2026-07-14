import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Meta / Instagram OAuth
META_APP_ID = os.getenv("META_APP_ID") or os.getenv("APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET") or os.getenv("APP_SECRET")
META_REDIRECT_URI = os.getenv("META_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/instagram/callback")
META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v19.0")

# JWT da aplicação
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "altere-esta-chave-em-producao")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))  # 7 dias

# Frontend (opcional): redirecionamento após login OAuth
FRONTEND_URL = os.getenv("FRONTEND_URL")

# Fallback: token global do .env (legado, sem login)
IG_USER_ID = os.getenv("IG_USER_ID")
USER_ACCESS_TOKEN = os.getenv("USER_ACCESS_TOKEN")
