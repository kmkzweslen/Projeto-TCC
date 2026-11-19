from app.utils.prompt_engineering import (
    REGRAS_LEGENDA,
    construir_prompt_imagem,
    construir_prompt_legenda,
    selecionar_cta,
)

PARAMS = {
    "tema": "lançamento da coleção de verão",
    "tipo": "imagem",
    "objetivo": "vender produto",
    "publico": "mulheres de 20 a 35 anos",
    "tom": "descontraído",
    "rede_alvo": "Instagram",
    "formato": "post de feed com imagem única",
}


def test_prompt_tem_os_seis_componentes_co_star_na_ordem():
    prompt = construir_prompt_legenda(PARAMS)
    secoes = ["(Context)", "(Objective)", "(Style)", "(Tone)", "(Audience)", "(Response)"]
    posicoes = [prompt.index(s) for s in secoes]
    assert posicoes == sorted(posicoes)


def test_prompt_usa_os_campos_de_entrada_e_as_regras():
    prompt = construir_prompt_legenda(PARAMS)
    for valor in ("lançamento da coleção de verão", "vender produto", "mulheres de 20 a 35 anos"):
        assert valor in prompt
    assert "Use um tom de voz descontraído." in prompt
    assert f"Entre {REGRAS_LEGENDA['caracteres_min']} e {REGRAS_LEGENDA['caracteres_max']}" in prompt
    assert "Exatamente uma chamada para ação" in prompt


def test_corrige_erros_do_prompt_antigo():
    prompt = construir_prompt_legenda(PARAMS)
    assert "Deslize" not in prompt and "Deslive" not in prompt
    assert "comunicação descontraído" not in prompt
    assert "maximizar o vender" not in prompt


def test_cta_unica_por_objetivo_ignorando_acentos():
    assert selecionar_cta("Promoção de inverno")[0] == "venda"
    assert selecionar_cta("educar o público")[0] == "salvar"
    assert selecionar_cta("atrair seguidores")[0] == "seguir"
    assert selecionar_cta("aumentar o engajamento")[0] == "comentar"
    assert selecionar_cta("fortalecer a marca")[0] == "visitar_perfil"
    assert selecionar_cta("algo sem palavra-chave")[0] == "salvar"
    for objetivo in ("vender", "educar", "inspirar", "marca"):
        exemplo = selecionar_cta(objetivo)[1]
        assert exemplo.count(".") == 1  # uma única frase de CTA


def test_prompt_de_imagem_proibe_texto_nos_dois_idiomas():
    pt = construir_prompt_imagem(PARAMS, idioma="pt")
    en = construir_prompt_imagem(PARAMS, idioma="en")
    assert "não deve conter textos" in pt and "quadrado (1:1)" in pt
    assert "must not contain any text" in en and "square (1:1)" in en
