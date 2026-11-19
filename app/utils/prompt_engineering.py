"""
Engenharia de prompt com o framework CO-STAR.

CO-STAR (GovTech Singapura) organiza a instrução em seis componentes:
  C - Context   (Contexto)  : cenário em que a resposta será usada
  O - Objective (Objetivo)  : o que a publicação deve alcançar
  S - Style     (Estilo)    : estilo de escrita
  T - Tone      (Tom)       : tom de voz
  A - Audience  (Público)   : a quem o texto se destina
  R - Response  (Resposta)  : formato e restrições da saída

As restrições do componente Response ficam em REGRAS_LEGENDA, que também é
usado por app/utils/conformidade.py para verificar se a legenda gerada as cumpre.
"""
import unicodedata
from typing import Dict, Tuple

# Restrições verificáveis da legenda (componente Response).
REGRAS_LEGENDA = {
    "caracteres_min": 100,
    "caracteres_max": 300,
    "emojis_min": 2,
    "emojis_max": 4,
    "hashtags_min": 3,
    "hashtags_max": 5,
    "ctas": 1,
}

MENSAGEM_SISTEMA = (
    "Você é um redator de mídias sociais. Siga exatamente o formato de resposta "
    "solicitado e responda somente com o texto final."
)

# Uma única CTA por objetivo: múltiplas chamadas na mesma mensagem tendem a
# reduzir o engajamento (Chae, 2021). As palavras-chave são comparadas sem acento.
_CTAS_POR_OBJETIVO: Tuple[Tuple[Tuple[str, ...], str, str], ...] = (
    (("vend", "produto", "compr", "promoc", "oferta", "lancamento"),
     "venda", "Garanta o seu pelo link na bio."),
    (("seguidor", "seguir", "crescer"),
     "seguir", "Siga o perfil para não perder os próximos conteúdos."),
    (("engaj", "interac", "comentar", "conversa"),
     "comentar", "Conte nos comentários o que você achou."),
    (("educ", "ensin", "inform", "dica", "explic"),
     "salvar", "Salve este post para consultar depois."),
    (("motiv", "inspir"),
     "compartilhar", "Compartilhe com alguém que precisa ler isso hoje."),
    (("marca", "branding", "fortalec", "institucional", "reconhec"),
     "visitar_perfil", "Visite nosso perfil e conheça mais sobre nós."),
)
_CTA_PADRAO = ("salvar", "Salve este post para ver depois.")


def _sem_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in normalizado if not unicodedata.combining(c)).lower()


def selecionar_cta(objetivo: str) -> Tuple[str, str]:
    """Retorna (tipo_cta, exemplo_cta) de acordo com o objetivo informado."""
    objetivo_norm = _sem_acentos(objetivo)
    for palavras, tipo, exemplo in _CTAS_POR_OBJETIVO:
        if any(p in objetivo_norm for p in palavras):
            return tipo, exemplo
    return _CTA_PADRAO


def _valor(params: Dict, campo: str, padrao: str) -> str:
    valor = (params.get(campo) or "").strip()
    return valor if valor else padrao


def construir_componentes_co_star(params: Dict) -> Dict[str, str]:
    """Monta o texto de cada componente CO-STAR a partir dos parâmetros de entrada."""
    rede = _valor(params, "rede_alvo", "Instagram")
    tema = _valor(params, "tema", "tema geral")
    objetivo = _valor(params, "objetivo", "engajar o público")
    tom = _valor(params, "tom", "descontraído")
    publico = _valor(params, "publico", "público geral")
    formato = _valor(params, "formato", "post de feed com imagem única")
    _, cta = selecionar_cta(objetivo)
    r = REGRAS_LEGENDA

    return {
        "context": (
            f"Você vai escrever a legenda de uma publicação para o {rede} sobre o tema "
            f"\"{tema}\". A imagem do post é gerada separadamente, por isso a legenda "
            f"não deve descrever detalhes visuais específicos."
        ),
        "objective": f"O objetivo da publicação é: {objetivo}.",
        "style": (
            f"Legenda para {rede} no formato \"{formato}\": comece com um gancho que "
            f"prenda a atenção logo nos primeiros caracteres, use frases curtas e "
            f"linguagem natural."
        ),
        "tone": f"Use um tom de voz {tom}.",
        "audience": (
            f"Público-alvo: {publico}. Use vocabulário e referências adequados a esse público."
        ),
        "response": (
            f"- Entre {r['caracteres_min']} e {r['caracteres_max']} caracteres no total, "
            f"contando emojis e hashtags.\n"
            f"- De {r['emojis_min']} a {r['emojis_max']} emojis.\n"
            f"- Exatamente uma chamada para ação (CTA), coerente com o objetivo. "
            f"Exemplo de CTA adequada: \"{cta}\"\n"
            f"- De {r['hashtags_min']} a {r['hashtags_max']} hashtags relevantes, "
            f"todas no final do texto.\n"
            f"- Responda apenas com o texto da legenda, sem título, aspas ou explicações."
        ),
    }


def construir_prompt_legenda(params: Dict) -> str:
    """Prompt de legenda estruturado nos seis componentes do CO-STAR."""
    c = construir_componentes_co_star(params)
    return (
        f"# CONTEXTO (Context)\n{c['context']}\n\n"
        f"# OBJETIVO (Objective)\n{c['objective']}\n\n"
        f"# ESTILO (Style)\n{c['style']}\n\n"
        f"# TOM (Tone)\n{c['tone']}\n\n"
        f"# PÚBLICO (Audience)\n{c['audience']}\n\n"
        f"# RESPOSTA (Response)\n{c['response']}"
    )


def construir_prompt_imagem(params: Dict, idioma: str = "pt") -> str:
    """
    Prompt de imagem: fotografia realista, quadrada (1:1), sem texto na imagem.
    O texto da publicação fica concentrado na legenda.
    """
    tema = _valor(params, "tema", "tema geral")
    publico = _valor(params, "publico", "público geral")
    rede = _valor(params, "rede_alvo", "Instagram")

    if idioma == "en":
        return (
            f"Realistic, professional photograph about \"{tema}\", designed to appeal to "
            f"{publico}, for a square (1:1) {rede} feed post. Natural lighting, realistic "
            f"colors, balanced composition, sharp focus. The image must not contain any "
            f"text, letters, numbers, logos or watermarks."
        )
    return (
        f"Fotografia realista e profissional sobre o tema \"{tema}\", pensada para atrair "
        f"o público {publico}, para um post de feed do {rede} em formato quadrado (1:1). "
        f"Iluminação natural, cores realistas, composição equilibrada e foco nítido. "
        f"A imagem não deve conter textos, letras, números, logotipos nem marcas d'água."
    )
