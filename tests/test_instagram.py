import pytest

from app.services import instagram_service as ig
from tests.conftest import RespostaFalsa

URL_IMG = "https://i.ibb.co/x.jpg"


@pytest.fixture
def graph(monkeypatch):
    """Simula a Graph API com respostas configuráveis por endpoint."""
    estado = {"status": ["IN_PROGRESS", "FINISHED"], "quota": (3, 100), "posts": []}

    def get(url, params, timeout):
        if url.endswith("content_publishing_limit"):
            usadas, total = estado["quota"]
            return RespostaFalsa(200, {"data": [{"quota_usage": usadas, "config": {"quota_total": total}}]})
        if url.endswith("/C1"):
            return RespostaFalsa(200, {"status_code": estado["status"].pop(0)})
        if url.endswith("/M1"):
            return RespostaFalsa(200, {"id": "M1", "permalink": "https://instagram.com/p/abc"})
        raise AssertionError(url)

    def post(url, data, timeout):
        estado["posts"].append(url)
        if url.endswith("/media"):
            return RespostaFalsa(200, {"id": "C1"})
        if url.endswith("/media_publish"):
            assert data["creation_id"] == "C1"
            return RespostaFalsa(200, {"id": "M1"})
        raise AssertionError(url)

    monkeypatch.setattr(ig.requests, "get", get)
    monkeypatch.setattr(ig.requests, "post", post)
    return estado


def test_publicacao_aguarda_status_finished(graph):
    esperas = []
    resultado = ig.publicar_no_feed(URL_IMG, "legenda", "IG1", "tok", dormir=esperas.append)
    assert resultado["media_id"] == "M1"
    assert resultado["permalink"] == "https://instagram.com/p/abc"
    assert len(esperas) == 1  # consultou IN_PROGRESS, esperou, recebeu FINISHED
    assert graph["posts"][-1].endswith("/media_publish")


def test_container_com_erro_nao_publica(graph):
    graph["status"] = ["ERROR"]
    resultado = ig.publicar_no_feed(URL_IMG, "legenda", "IG1", "tok", dormir=lambda s: None)
    assert resultado["etapa"] == "processar_container"
    assert not any(u.endswith("/media_publish") for u in graph["posts"])


def test_limite_diario_atingido(graph):
    graph["quota"] = (100, 100)
    resultado = ig.publicar_no_feed(URL_IMG, "legenda", "IG1", "tok")
    assert resultado["etapa"] == "limite" and graph["posts"] == []


def test_validacoes_antes_de_chamar_a_api(graph):
    assert ig.publicar_no_feed("http://inseguro.jpg", "x", "IG1", "tok")["etapa"] == "validacao"
    assert ig.publicar_no_feed(URL_IMG, "x" * 2201, "IG1", "tok")["etapa"] == "validacao"
    assert graph["posts"] == []


def test_timeout_do_container():
    relogio = iter([0, 0, 100])
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(ig.requests, "get", lambda *a, **k: RespostaFalsa(200, {"status_code": "IN_PROGRESS"}))
        with pytest.raises(ig.ErroPublicacao, match="não ficou pronto"):
            ig.aguardar_container("C1", "tok", intervalo_s=1, timeout_s=10,
                                  dormir=lambda s: None, relogio=lambda: next(relogio))
