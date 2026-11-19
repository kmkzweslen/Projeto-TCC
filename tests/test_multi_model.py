import time

from app.services.multi_model_service import gerar_conteudo_multi_modelo

PARAMS = {"tema": "café", "tipo": "imagem", "objetivo": "fortalecer a marca",
          "publico": "estudantes", "tom": "acolhedor"}
LEGENDA_OK = ("☕ Nosso café é feito com carinho para aquecer seus dias de estudo 📚 "
              "Visite nosso perfil e conheça mais sobre nós. #cafe #estudos #cafeteria")


class Provedor:
    def __init__(self, nome, espera=0.0, falha=False, saida=b"img"):
        self.NOME, self.espera, self.falha, self.saida = nome, espera, falha, saida

    def disponivel(self):
        return True

    def modelo(self):
        return f"{self.NOME}-modelo"

    def _rodar(self):
        time.sleep(self.espera)
        if self.falha:
            raise RuntimeError(f"{self.NOME} falhou")
        return self.saida

    def gerar_imagem(self, prompt):
        return self._rodar()

    def gerar_texto(self, prompt, sistema):
        return self._rodar()


def hospedar_falso(conteudo):
    return {"public_url": "https://i.ibb.co/x.jpg"}


def test_falha_isolada_e_combinacoes():
    resultado = gerar_conteudo_multi_modelo(
        PARAMS,
        provedores_imagem=[(Provedor("img-a"), "pt"), (Provedor("img-b", falha=True), "en")],
        provedores_texto=[Provedor("txt-a", saida=LEGENDA_OK), Provedor("txt-b", saida=LEGENDA_OK)],
        hospedar=hospedar_falso,
    )
    assert len(resultado["imagens"]) == 1 and len(resultado["imagens_falhas"]) == 1
    assert resultado["imagens_falhas"][0]["error"] == "img-b falhou"
    assert len(resultado["legendas"]) == 2
    assert resultado["total_combinacoes"] == 2
    assert resultado["legendas"][0]["conformidade"]["conforme"] is True
    assert all("tempo_s" in item for item in resultado["imagens"] + resultado["legendas"])


def test_texto_e_imagem_rodam_em_paralelo():
    inicio = time.perf_counter()
    gerar_conteudo_multi_modelo(
        PARAMS,
        provedores_imagem=[(Provedor("img", espera=0.4), "pt")],
        provedores_texto=[Provedor("txt", espera=0.4, saida=LEGENDA_OK)],
        hospedar=hospedar_falso,
    )
    assert time.perf_counter() - inicio < 0.75  # sequencial levaria ~0,8 s


def test_timeout_nao_segura_a_resposta():
    inicio = time.perf_counter()
    resultado = gerar_conteudo_multi_modelo(
        PARAMS,
        provedores_imagem=[(Provedor("lento", espera=3), "pt")],
        provedores_texto=[Provedor("txt", saida=LEGENDA_OK)],
        hospedar=hospedar_falso,
        timeout_s=0.5,
    )
    assert time.perf_counter() - inicio < 1.5
    assert "Tempo-limite" in resultado["imagens_falhas"][0]["error"]
    assert len(resultado["legendas"]) == 1


def test_tipo_texto_nao_gera_imagem():
    img = Provedor("img")
    resultado = gerar_conteudo_multi_modelo(
        {**PARAMS, "tipo": "texto"},
        provedores_imagem=[(img, "pt")],
        provedores_texto=[Provedor("txt", saida=LEGENDA_OK)],
        hospedar=hospedar_falso,
    )
    assert resultado["imagens"] == [] and resultado["imagens_falhas"] == []
    assert resultado["total_combinacoes"] == 1
