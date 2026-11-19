"""
Configuração central da aplicação.

Todas as variáveis de ambiente são lidas aqui, para que os serviços não
precisem chamar os.getenv() espalhados pelo código. Valores sensíveis
(chaves de API, segredos) nunca têm valor padrão real.
"""
import os
import warnings
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()


def _env(nome: str, padrao: Optional[str] = None) -> Optional[str]:
    """Lê uma variável de ambiente, tratando string vazia como ausente."""
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    valor = valor.strip()
    return valor if valor else padrao


def _env_int(nome: str, padrao: int) -> int:
    try:
        return int(_env(nome, str(padrao)))
    except (TypeError, ValueError):
        return padrao


def _env_float(nome: str, padrao: Optional[float]) -> Optional[float]:
    valor = _env(nome)
    if valor is None:
        return padrao
    try:
        return float(valor)
    except ValueError:
        return padrao


def _env_lista(nome: str, padrao: str = "") -> List[str]:
    return [item.strip() for item in (_env(nome, padrao) or "").split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Ambiente
# ---------------------------------------------------------------------------
APP_ENV = (_env("APP_ENV", "development") or "development").lower()

# ---------------------------------------------------------------------------
# Meta / Instagram
# ---------------------------------------------------------------------------
META_APP_ID = _env("META_APP_ID") or _env("APP_ID")
META_APP_SECRET = _env("META_APP_SECRET") or _env("APP_SECRET")
META_REDIRECT_URI = _env("META_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/instagram/callback")
# A v19.0 expirou em 21/05/2026. A v26.0 foi lançada em 29/07/2026.
META_GRAPH_VERSION = _env("META_GRAPH_VERSION", "v26.0")
# Opcional (Login do Facebook para Empresas): id da "Configuração" criada no
# painel do app. Se definido, o login usa config_id em vez da lista de scopes.
META_LOGIN_CONFIG_ID = _env("META_LOGIN_CONFIG_ID")
# Permissões pedidas no login (quando não há config_id), separadas por vírgula.
# business_management ficou de fora do padrão: em apps com o caso de uso
# "Instagram" a Meta recusa o login com "Invalid Scope: business_management".
META_LOGIN_SCOPES = [
    s.strip() for s in _env(
        "META_LOGIN_SCOPES",
        "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement",
    ).split(",") if s.strip()
]

# Publicação: consulta do estado do contêiner antes de publicar
IG_STATUS_POLL_INTERVAL_S = _env_float("IG_STATUS_POLL_INTERVAL_S", 3.0)
IG_STATUS_POLL_TIMEOUT_S = _env_float("IG_STATUS_POLL_TIMEOUT_S", 90.0)

# Fallback legado (sem login OAuth)
IG_USER_ID = _env("IG_USER_ID")
USER_ACCESS_TOKEN = _env("USER_ACCESS_TOKEN")

# ---------------------------------------------------------------------------
# Autenticação da API (JWT) e criptografia de tokens
# ---------------------------------------------------------------------------
_SEGREDOS_INSEGUROS = {
    "",
    "altere-esta-chave-em-producao",
    "uma-chave-secreta-longa-e-aleatoria",
}
JWT_SECRET_KEY = _env("JWT_SECRET_KEY", "") or ""
# Em desenvolvimento, sem segredo configurado, gera um segredo temporário.
# Consequência: os logins (e os tokens criptografados) deixam de valer ao reiniciar.
JWT_SECRET_EFEMERO = False
if not JWT_SECRET_KEY and APP_ENV != "production":
    import secrets as _secrets

    JWT_SECRET_KEY = _secrets.token_urlsafe(48)
    JWT_SECRET_EFEMERO = True
JWT_ALGORITHM = "HS256"
# Duração da sessão no sistema. Padrão: 30 dias. O limite é 60 dias (1440 h),
# que é a validade do token de longa duração da Meta: uma sessão mais longa
# que isso continuaria "logada" sem conseguir publicar.
JWT_EXPIRE_HOURS_MAX = 1440
JWT_EXPIRE_HOURS = _env_int("JWT_EXPIRE_HOURS", 720)
if JWT_EXPIRE_HOURS > JWT_EXPIRE_HOURS_MAX:
    warnings.warn(
        f"JWT_EXPIRE_HOURS={JWT_EXPIRE_HOURS} passa de 60 dias (validade do token da Meta); "
        f"usando {JWT_EXPIRE_HOURS_MAX}."
    )
    JWT_EXPIRE_HOURS = JWT_EXPIRE_HOURS_MAX
elif JWT_EXPIRE_HOURS < 1:
    JWT_EXPIRE_HOURS = 720

# Chave Fernet para criptografar os tokens da Meta salvos no banco.
# Se ausente, é derivada do JWT_SECRET_KEY (ver app/utils/criptografia.py).
TOKEN_ENCRYPTION_KEY = _env("TOKEN_ENCRYPTION_KEY")

# ---------------------------------------------------------------------------
# Front-end e CORS
# ---------------------------------------------------------------------------
FRONTEND_URL = _env("FRONTEND_URL")
CORS_ORIGINS = _env_lista(
    "CORS_ORIGINS",
    ",".join(filter(None, [FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"])),
)

# ---------------------------------------------------------------------------
# Provedores de IA
# ---------------------------------------------------------------------------
OPENAI_API_KEY = _env("OPENAI_API_KEY")
OPENAI_BASE_URL = _env("OPENAI_BASE_URL", "https://api.openai.com/v1")
# gpt-3.5-turbo foi desligado em 23/10/2026; substituto indicado: gpt-5.6-terra.
OPENAI_TEXT_MODEL = _env("OPENAI_TEXT_MODEL", "gpt-5.6-terra")
# Família DALL·E retirada em 12/05/2026. GPT Image 2.6 Flare = variante rápida.
OPENAI_IMAGE_MODEL = _env("OPENAI_IMAGE_MODEL", "gpt-image-2.6-flare")
OPENAI_IMAGE_SIZE = _env("OPENAI_IMAGE_SIZE", "1024x1024")
OPENAI_IMAGE_QUALITY = _env("OPENAI_IMAGE_QUALITY")  # opcional; só é enviado se definido

GEMINI_API_KEY = _env("GEMINI_API_KEY")
GEMINI_BASE_URL = _env("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
# Família 1.5 retirada em 2025. No diagnóstico de 18/11/2026, gemini-3.5-flash-lite
# respondeu em ~1 s e gemini-3.6-flash em ~108 s (acima do tempo-limite), por isso
# o flash-lite é o padrão. O fallback só é usado se o modelo principal não existir (404).
GEMINI_TEXT_MODEL = _env("GEMINI_TEXT_MODEL", "gemini-3.5-flash-lite")
GEMINI_FALLBACK_MODELS = _env_lista("GEMINI_FALLBACK_MODELS", "gemini-3.6-flash")

STABILITY_API_KEY = _env("STABILITY_AI_API_KEY") or _env("STABILITY_API_KEY")
# O endpoint v1 do SDXL foi substituído pela API Stable Image (v2beta).
STABILITY_ENDPOINT = _env(
    "STABILITY_ENDPOINT", "https://api.stability.ai/v2beta/stable-image/generate/core"
)

# Temperatura: os modelos atuais (GPT-5.6 e Gemini 3.6+) rejeitam ou descartam
# parâmetros de amostragem. Só é enviada se definida explicitamente.
LLM_TEMPERATURE = _env_float("LLM_TEMPERATURE", None)

# Tempos-limite (segundos)
TEXT_TIMEOUT_S = _env_float("TEXT_TIMEOUT_S", 60.0)
IMAGE_TIMEOUT_S = _env_float("IMAGE_TIMEOUT_S", 120.0)
GENERATION_TIMEOUT_S = _env_float("GENERATION_TIMEOUT_S", 150.0)

# ---------------------------------------------------------------------------
# Hospedagem de imagens e banco
# ---------------------------------------------------------------------------
IMGBB_API_KEY = _env("IMGBB_API_KEY")
MONGODB_URI = _env("MONGODB_URI")
MONGODB_DB_NAME = _env("MONGODB_DB_NAME", "prototipo")


def jwt_secret_inseguro() -> bool:
    return JWT_SECRET_KEY in _SEGREDOS_INSEGUROS or len(JWT_SECRET_KEY) < 32


def validar_configuracao() -> None:
    """
    Verifica a configuração na inicialização.

    Em produção (APP_ENV=production), um segredo JWT fraco impede a subida da
    aplicação. Em desenvolvimento, apenas emite um aviso.
    """
    if JWT_SECRET_EFEMERO:
        warnings.warn(
            "JWT_SECRET_KEY não definido: usando segredo temporário. "
            "Os logins deixam de valer quando o servidor reinicia.",
            RuntimeWarning,
            stacklevel=2,
        )
        return
    if jwt_secret_inseguro():
        mensagem = (
            "JWT_SECRET_KEY ausente, padrão ou com menos de 32 caracteres. "
            "Gere uma com: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
        if APP_ENV == "production":
            raise RuntimeError(mensagem)
        warnings.warn(mensagem, RuntimeWarning, stacklevel=2)
