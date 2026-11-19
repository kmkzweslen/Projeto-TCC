"""
Verificação automática da legenda contra o componente Response do CO-STAR
(critério C5 do artigo).

As regras vêm de REGRAS_LEGENDA (prompt_engineering.py), para que o prompt e a
verificação usem exatamente os mesmos limites.

Observação: a detecção de CTA é heurística (procura verbos/expressões típicas
de chamada para ação em cada frase). Os demais itens são contagens exatas.
"""
import re
import unicodedata
from typing import Dict

from app.utils.prompt_engineering import REGRAS_LEGENDA

_HASHTAG = re.compile(r"#\w+", re.UNICODE)
_HASHTAGS_NO_FINAL = re.compile(r"(?:\s*#\w+)+\s*$", re.UNICODE)

_FAIXAS_EMOJI = (
    (0x1F300, 0x1FAFF),  # símbolos, pictogramas, emoticons, transporte, suplementares
    (0x1F000, 0x1F2FF),  # mahjong, cartas, alfanuméricos fechados
    (0x2600, 0x27BF),    # símbolos diversos e dingbats
    (0x2300, 0x23FF),    # técnicos (⌚, ⏰...)
    (0x2B00, 0x2BFF),    # setas e estrelas (⭐...)
)
_MODIFICADORES = set(range(0x1F3FB, 0x1F400)) | {0xFE0F, 0xFE0E, 0x20E3}
_ZWJ = 0x200D
_INDICADOR_REGIONAL = (0x1F1E6, 0x1F1FF)

_PADROES_CTA = re.compile(
    r"\b(?:salve|salva|compartilhe|compartilha|siga|segue a gente|comente|comenta|"
    r"nos comentarios|acesse|clique|toque no|garanta|visite|marque|chame|"
    r"entre em contato|fale com|confira|link na bio|mande|envie|deixe seu|deixe sua|"
    r"participe|inscreva|reserve|peca ja|peca o seu|compre|experimente|venha|"
    r"aproveite|conte pra gente|conte para)\b"
)
_PREAMBULOS = ("legenda:", "aqui esta", "segue a legenda", "claro!", "claro,")


def _sem_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normalizado if not unicodedata.combining(c)).lower()


def contar_emojis(texto: str) -> int:
    """Conta emojis, tratando sequências (ZWJ, tons de pele, bandeiras) como um só."""
    total = 0
    anterior_zwj = False
    regional_pendente = False
    for caractere in texto:
        cp = ord(caractere)
        if cp == _ZWJ:
            anterior_zwj = True
            continue
        if cp in _MODIFICADORES:
            continue
        if _INDICADOR_REGIONAL[0] <= cp <= _INDICADOR_REGIONAL[1]:
            if regional_pendente:
                regional_pendente = False  # segundo indicador da bandeira
            else:
                total += 1
                regional_pendente = True
            anterior_zwj = False
            continue
        regional_pendente = False
        if any(inicio <= cp <= fim for inicio, fim in _FAIXAS_EMOJI):
            if not anterior_zwj:
                total += 1
        anterior_zwj = False
    return total


def contar_ctas(texto: str) -> int:
    """Número de frases que contêm uma chamada para ação (heurística)."""
    sem_hashtags = _HASHTAG.sub(" ", texto)
    frases = re.split(r"[.!?\n]+", sem_hashtags)
    total = 0
    for frase in frases:
        if _PADROES_CTA.search(_sem_acentos(frase)):
            total += 1
    return total


def verificar_legenda(legenda: str) -> Dict:
    """Verifica a legenda e retorna as contagens, o resultado de cada regra e o geral."""
    texto = (legenda or "").strip()
    r = REGRAS_LEGENDA

    caracteres = len(texto)
    emojis = contar_emojis(texto)
    hashtags = _HASHTAG.findall(texto)
    final = _HASHTAGS_NO_FINAL.search(texto)
    hashtags_no_final = len(_HASHTAG.findall(final.group(0))) if final else 0
    ctas = contar_ctas(texto)
    inicio = _sem_acentos(texto[:40])
    sem_preambulo = not (
        texto[:1] in ('"', "“", "'", "*")
        or any(inicio.startswith(p) for p in _PREAMBULOS)
    )

    regras = {
        "tamanho": r["caracteres_min"] <= caracteres <= r["caracteres_max"],
        "emojis": r["emojis_min"] <= emojis <= r["emojis_max"],
        "hashtags": r["hashtags_min"] <= len(hashtags) <= r["hashtags_max"],
        "hashtags_no_final": len(hashtags) > 0 and hashtags_no_final == len(hashtags),
        "cta_unica": ctas == r["ctas"],
        "sem_preambulo": sem_preambulo,
    }
    return {
        "caracteres": caracteres,
        "emojis": emojis,
        "hashtags": len(hashtags),
        "ctas_detectadas": ctas,
        "regras": regras,
        "conforme": all(regras.values()),
    }
