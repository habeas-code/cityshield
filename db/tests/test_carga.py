"""Testes da carga (#10) na parte que não precisa de banco:
ler os arquivos e montar as linhas que vão para as tabelas."""

import json

import pytest

import carga
from carga import ErroCarga


def colecao(*feicoes, **topo):
    return {"type": "FeatureCollection", **topo, "features": list(feicoes)}


def feicao(geometria, **propriedades):
    return {"type": "Feature", "properties": propriedades, "geometry": geometria}


PONTO = {"type": "Point", "coordinates": [-47.45, -23.47]}
POLIGONO = {
    "type": "Polygon",
    "coordinates": [[[-47.45, -23.47], [-47.44, -23.47], [-47.44, -23.46], [-47.45, -23.47]]],
}


def escrever(pasta, nome, conteudo):
    caminho = pasta / nome
    caminho.write_text(json.dumps(conteudo), encoding="utf-8")
    return caminho


# ---------------------------------------------------------------- arquivos reais


def test_arquivos_de_docs_dados_viram_uma_linha_por_feicao():
    camadas = carga.montar_camadas()

    assert camadas.keys() == {"risco", "drenagem", "ruas", "areas"}
    for camada, arquivo in carga.ARQUIVOS.items():
        feicoes = carga.ler_geojson(carga.PASTA_DADOS / arquivo)["features"]
        assert len(camadas[camada]["linhas"]) == len(feicoes) >= 1


def test_meta_das_recomendacoes_guarda_fonte_aviso_e_parametros():
    meta = carga.montar_camadas()["areas"]["meta"]

    assert {"fonte", "area", "aviso", "metodo", "parametros"} <= meta.keys()
    assert "features" not in meta and "type" not in meta


# ---------------------------------------------------------------- leitura


def test_ler_geojson_recusa_o_que_nao_e_featurecollection(tmp_path):
    caminho = escrever(tmp_path, "x.geojson", {"type": "Feature"})

    with pytest.raises(ErroCarga, match="não é uma FeatureCollection"):
        carga.ler_geojson(caminho)


def test_ler_geojson_avisa_arquivo_que_falta(tmp_path):
    with pytest.raises(ErroCarga, match="não encontrado"):
        carga.ler_geojson(tmp_path / "sumiu.geojson")


def test_recusa_qualquer_arquivo_em_dados_privados(tmp_path):
    privada = tmp_path / "dados_privados"
    privada.mkdir()
    caminho = escrever(privada, "ruas.geojson", colecao())

    with pytest.raises(ErroCarga, match="dados_privados"):
        carga.ler_geojson(caminho)


# ---------------------------------------------------------------- linhas


def test_linha_guarda_todas_as_propriedades_e_a_geometria_original():
    original = feicao(POLIGONO, classe="alto", hand_min_m=0.0, hand_max_m=5.0)

    linha = carga.linha_risco(original)

    assert linha["classe"] == "alto"
    assert json.loads(linha["propriedades"]) == original["properties"]
    assert json.loads(linha["geom"]) == POLIGONO


def test_drenagem_mantem_multilinestring():
    multi = {"type": "MultiLineString", "coordinates": [[[0, 0], [1, 1]], [[2, 2], [3, 3]]]}

    linha = carga.linha_drenagem({"type": "Feature", "properties": {}, "geometry": multi})

    assert json.loads(linha["geom"])["type"] == "MultiLineString"
    assert linha["propriedades"] == "{}"


def test_acentos_ficam_legiveis_no_jsonb():
    linha = carga.linha_ruas(feicao(PONTO, rua="Rua São João", registros=3))

    assert "São João" in linha["propriedades"]
    assert linha["rua"] == "Rua São João" and linha["registros"] == 3


def test_area_usa_id_nota_e_posicao():
    linha = carga.linha_areas(
        {**feicao(POLIGONO, id="way-1", solucao="jardim_chuva", nota=80, posicao=1), "id": "way-1"}
    )

    assert (linha["id"], linha["solucao"], linha["nota"], linha["posicao"]) == (
        "way-1",
        "jardim_chuva",
        80,
        1,
    )


def test_area_com_dois_ids_diferentes_e_recusada():
    errada = {**feicao(POLIGONO, id="way-1", solucao="x", nota=1, posicao=1), "id": "way-2"}

    with pytest.raises(ErroCarga, match="dois ids"):
        carga.linha_areas(errada)


def test_feicao_sem_geometria_e_recusada():
    with pytest.raises(ErroCarga, match="sem geometria"):
        carga.linha_drenagem({"type": "Feature", "properties": {}, "geometry": None})


# ---------------------------------------------------------------- contagens


def test_quantidade_nova_de_feicoes_nao_quebra_a_carga(tmp_path, monkeypatch):
    # O pipeline mudou e agora gera 2 ruas: a carga acompanha o arquivo.
    monkeypatch.setattr(carga, "ARQUIVOS", {"ruas": "ruas.geojson"})
    escrever(
        tmp_path,
        "ruas.geojson",
        colecao(feicao(PONTO, rua="A", registros=1), feicao(PONTO, rua="B", registros=2)),
    )

    assert len(carga.montar_camadas(tmp_path)["ruas"]["linhas"]) == 2


def test_arquivo_sem_feicoes_e_recusado(tmp_path, monkeypatch):
    monkeypatch.setattr(carga, "ARQUIVOS", {"ruas": "ruas.geojson"})
    escrever(tmp_path, "ruas.geojson", colecao())

    with pytest.raises(ErroCarga, match="ruas.geojson não tem nenhuma feição"):
        carga.montar_camadas(tmp_path)


def test_banco_com_linhas_a_menos_ou_a_mais_e_recusado():
    with pytest.raises(ErroCarga, match="o arquivo tem 79 feições, mas o banco ficou com 78"):
        carga.conferir_banco("ruas", no_banco=78, no_arquivo=79)
    with pytest.raises(ErroCarga, match="ficou com 80"):
        carga.conferir_banco("ruas", no_banco=80, no_arquivo=79)


def test_banco_igual_ao_arquivo_passa():
    carga.conferir_banco("ruas", no_banco=79, no_arquivo=79)


def test_propriedade_que_falta_diz_qual_e(tmp_path, monkeypatch):
    monkeypatch.setattr(carga, "ARQUIVOS", {"ruas": "ruas.geojson"})
    escrever(tmp_path, "ruas.geojson", colecao(feicao(PONTO, rua="A")))

    with pytest.raises(ErroCarga, match="registros"):
        carga.montar_camadas(tmp_path)
