"""
Diagnóstico rápido do Gemini: testa cada modelo configurado com um prompt
curto e um tempo-limite longo, mostrando o tempo de resposta e o erro (se houver).

Uso (na raiz do projeto):
    python -m scripts.diagnostico_gemini
"""
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import config  # noqa: E402

TIMEOUT_S = 180


def testar(modelo: str) -> None:
    url = f"{config.GEMINI_BASE_URL}/models/{modelo}:generateContent"
    corpo = {"contents": [{"role": "user", "parts": [{"text": "Responda apenas com a palavra: ok"}]}]}
    print(f"\n▶ {modelo}")
    inicio = time.perf_counter()
    try:
        resposta = requests.post(
            url, headers={"x-goog-api-key": config.GEMINI_API_KEY}, json=corpo, timeout=TIMEOUT_S
        )
        tempo = time.perf_counter() - inicio
        print(f"   HTTP {resposta.status_code} em {tempo:.1f} s")
        if resposta.ok:
            dados = resposta.json()
            partes = ((dados.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
            texto = "".join(p.get("text", "") for p in partes if not p.get("thought"))
            print(f"   Resposta: {texto.strip()[:100]!r}")
            uso = dados.get("usageMetadata") or {}
            if uso:
                print(f"   Tokens de raciocínio: {uso.get('thoughtsTokenCount', 0)}")
        else:
            print(f"   Erro: {resposta.text[:400]}")
    except requests.RequestException as e:
        print(f"   Falhou após {time.perf_counter() - inicio:.1f} s: {e}")


def main():
    if not config.GEMINI_API_KEY:
        print("GEMINI_API_KEY não está definido no .env")
        return
    modelos = [config.GEMINI_TEXT_MODEL] + [
        m for m in config.GEMINI_FALLBACK_MODELS if m != config.GEMINI_TEXT_MODEL
    ]
    for modelo in modelos:
        testar(modelo)


if __name__ == "__main__":
    main()
