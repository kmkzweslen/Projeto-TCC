from app.utils.conformidade import contar_ctas, contar_emojis, verificar_legenda

BOA = (
    "☀️ A coleção de verão chegou e está linda! Peças leves para você brilhar nos dias "
    "quentes 👗 Garanta a sua pelo link na bio. #verao #moda #lookdodia"
)


def test_legenda_conforme():
    resultado = verificar_legenda(BOA)
    assert resultado["conforme"], resultado
    assert resultado["emojis"] == 2 and resultado["hashtags"] == 3 and resultado["ctas_detectadas"] == 1


def test_emojis_compostos_contam_como_um():
    assert contar_emojis("💪🏽") == 1          # tom de pele
    assert contar_emojis("👨‍👩‍👧") == 1         # sequência ZWJ
    assert contar_emojis("🇧🇷") == 1           # bandeira
    assert contar_emojis("☀️☀️") == 2          # seletor de variação


def test_cta_por_palavra_inteira():
    assert contar_ctas("Consiga resultados e persiga seus sonhos") == 0
    assert contar_ctas("Salve este post. Siga o perfil!") == 2


def test_regras_violadas():
    resultado = verificar_legenda('Legenda: "texto curto" #a')
    regras = resultado["regras"]
    assert not regras["tamanho"] and not regras["hashtags"] and not regras["sem_preambulo"]
    assert not resultado["conforme"]


def test_hashtags_fora_do_final():
    texto = "Olá #meio " + "x" * 120 + " 😀😀 Salve este post. #a #b #c"
    assert verificar_legenda(texto)["regras"]["hashtags_no_final"] is False
