"""Teste do site no navegador: as quatro abas do mapa.html sem erro no console,
e os números que aparecem na tela iguais aos dos arquivos de docs/dados/.

Rodar da raiz do repositório:
    pip install -r tests/site/requirements.txt
    python -m playwright install --with-deps chromium
    python -m pytest -q tests/site
"""

import json
import math
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect, sync_playwright

DOCS = Path(__file__).resolve().parents[2] / "docs"

# Serviços de fora que podem falhar no CI (mapa de fundo, fontes, satélite).
# Só esses são bloqueados; os arquivos de docs/ sempre carregam.
DE_FORA = (
    "basemaps.cartocdn.com",
    "tiles.openfreemap.org",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "server.arcgisonline.com",
)

TELAS = {
    "computador": {"width": 1366, "height": 900},
    "celular": {"width": 390, "height": 844},
}


def de_fora(url):
    host = urlparse(url or "").hostname or ""
    return any(host == d or host.endswith("." + d) for d in DE_FORA)


@pytest.fixture(scope="module")
def site():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    servidor = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(porta), "-b", "127.0.0.1", "-d", str(DOCS)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{porta}"
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(url + "/mapa.html", timeout=1)
                break
            except OSError:
                time.sleep(0.1)
        else:
            pytest.fail("o http.server não subiu")
        yield url
    finally:
        servidor.terminate()
        servidor.wait()


@pytest.fixture(scope="module")
def navegador():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.mark.parametrize("tela", TELAS)
def test_quatro_abas_sem_erro(site, navegador, tela):
    contexto = navegador.new_context(viewport=TELAS[tela])
    contexto.route(lambda url: de_fora(url), lambda rota: rota.abort())
    pagina = contexto.new_page()
    erros = []
    pagina.on("pageerror", lambda e: erros.append(f"exceção: {e}"))

    def no_console(msg):
        if msg.type == "error" and not de_fora(msg.location.get("url")):
            erros.append(f"console: {msg.text}")

    pagina.on("console", no_console)

    try:
        pagina.goto(site + "/mapa.html")
        expect(pagina.locator("#mapa canvas.maplibregl-canvas")).to_be_visible(timeout=20_000)

        abas = pagina.locator("header .abas")
        for nome in ("Diagnóstico", "Oportunidades", "Simulação", "Sobre"):
            aba = abas.get_by_role("tab", name=nome)
            aba.click()
            expect(aba).to_have_attribute("aria-selected", "true")

        abas.get_by_role("tab", name="Oportunidades").click()
        primeira = pagina.locator("#fila li button").first
        expect(primeira).to_be_visible(timeout=20_000)
        primeira.click()
        if tela == "celular":
            expect(pagina.locator(".maplibregl-popup")).to_be_visible()
        else:
            expect(pagina.locator("#det-area")).to_be_visible()

        abas.get_by_role("tab", name="Simulação").click()
        volta = pagina.locator("#c-chuva-volta")
        antes = volta.text_content()
        pagina.locator("#c-chuva").fill("100")
        expect(volta).not_to_have_text(antes or "")

        pagina.wait_for_timeout(500)
        assert not erros, "\n".join(erros)
    finally:
        contexto.close()


# ---------------------------------------------------------------- números da tela

DADOS = DOCS / "dados"


def _json(nome):
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def _pct(x):
    """Igual ao site: Math.round(x * 100) + '%' (Math.round arredonda .5 para cima)."""
    return f"{math.floor(x * 100 + 0.5)}%"


def _milhar(x):
    """Igual ao site: Math.round(x).toLocaleString('pt-BR')."""
    return f"{math.floor(x + 0.5):,}".replace(",", ".")


def _cenario_50mm():
    """A conta da Simulação com 50 mm, refeita aqui a partir dos parâmetros do arquivo
    (docs/recomendacoes.md, "Cenário antes e depois"), sem usar o código do site."""
    g = _json("recomendacoes.geojson")
    par, mm = g["parametros"], 50
    chega = retida = 0.0
    for f in g["features"]:
        p, a = f["properties"], f["properties"]["area_m2"]
        if p["solucao"] == "piso_permeavel":
            c, r = a * mm / 1000, a * min(mm, par["piso_capacidade_mm"]) / 1000
        elif p["solucao"] == "telhado_verde":
            c = a * mm / 1000
            r = c * par["telhado_retencao"]
        elif p["solucao"] == "jardim_chuva":
            j = a * par["jardim_fracao_da_area"]
            c = j * par["jardim_area_que_escoa"] * mm / 1000
            r = min(c, j * par["jardim_lamina_m"])
        else:
            continue  # parque: capacidade, fora da conta
        chega += c
        retida += r
    return chega, retida, g


def test_numeros_do_site_batem_com_os_arquivos(site, navegador):
    """O que a pessoa lê na tela é o que está nos arquivos de docs/dados/."""
    contexto = navegador.new_context(viewport=TELAS["computador"])
    contexto.route(lambda url: de_fora(url), lambda rota: rota.abort())
    pagina = contexto.new_page()
    try:
        pagina.goto(site + "/mapa.html")
        expect(pagina.locator("#mapa canvas.maplibregl-canvas")).to_be_visible(timeout=20_000)

        # Quadro "O mapa bate com a realidade?": validação de 2022-2023
        cidade = _json("validacao.json")["cidade"]
        expect(pagina.locator("#v-reg")).to_have_text(_pct(cidade["fracao_registros"]["alto"]))
        expect(pagina.locator("#v-ruas")).to_have_text(_pct(cidade["fracao_ruas"]["alto"]))

        # ... e o bloco de depois do mapa pronto (registros oficiais, LAI)
        depois = _json("lai_defesa_civil.json")["grupos"]["depois_do_mapa"]
        h, c = depois["hand"]["cidade"], depois["carta"]["cidade"]
        expect(pagina.locator("#l-reg")).to_have_text(_pct(h["fracao_registros"]["alto"] + h["fracao_registros"]["medio"]))
        expect(pagina.locator("#l-carta")).to_have_text(_pct(1 - c["fracao_registros"]["fora"]))
        expect(pagina.locator("#l-n")).to_have_text(str(round(h["registros_considerados"])))

        # Fila: a 1ª da lista é a de maior nota, e a ficha mostra a mesma conta
        chega, retida, recs = _cenario_50mm()
        maior = max(f["properties"]["nota"] for f in recs["features"])
        abas = pagina.locator("header .abas")
        abas.get_by_role("tab", name="Oportunidades").click()
        pagina.locator("#fila li button").first.click()
        expect(pagina.locator("#det-area .pa-conta").first).to_have_text(re.compile(rf"= {maior}$"))

        # Simulação, chuva padrão de 50 mm: água que chega e retida
        abas.get_by_role("tab", name="Simulação").click()
        kpis = pagina.locator("#c-kpis")
        expect(kpis).to_contain_text(f"{_milhar(chega)} m³")
        expect(kpis).to_contain_text(f"{_milhar(retida)} m³({math.floor(retida / chega * 100 + 0.5)}%)")
    finally:
        contexto.close()


def test_links_de_baixar_os_dados_existem(site):
    """Todo arquivo da lista "Baixar os dados" (aba Sobre) existe no site publicado."""
    html = (DOCS / "mapa.html").read_text(encoding="utf-8")
    links = re.findall(r'<a href="(dados/[^"]+)" download>', html)
    assert len(links) >= 5
    for caminho in links:
        with urllib.request.urlopen(f"{site}/{caminho}", timeout=5) as resposta:
            assert resposta.status == 200, caminho


def test_pagina_inicial_mostra_os_numeros_da_validacao(site, navegador):
    """A seção "O mapa acerta?" do index.html lê os mesmos arquivos do mapa."""
    contexto = navegador.new_context(viewport=TELAS["computador"])
    contexto.route(lambda url: de_fora(url), lambda rota: rota.abort())
    pagina = contexto.new_page()
    erros = []
    pagina.on("pageerror", lambda e: erros.append(f"exceção: {e}"))
    try:
        pagina.goto(site + "/index.html")
        cidade = _json("validacao.json")["cidade"]
        expect(pagina.locator("#i-v-reg")).to_have_text(_pct(cidade["fracao_registros"]["alto"]))
        lai = _json("lai_defesa_civil.json")
        h = lai["grupos"]["depois_do_mapa"]["hand"]["cidade"]
        expect(pagina.locator("#i-l-reg")).to_have_text(_pct(h["fracao_registros"]["alto"] + h["fracao_registros"]["medio"]))
        local = lai["comparacao_local"]["regiao"]["depois_do_mapa"]["hand"]["cidade"]
        vezes = f"{local['vezes_acima_do_acaso_alto_medio']:.1f}".replace(".", ",") + "×"
        expect(pagina.locator("#i-l-local")).to_have_text(vezes)
        assert not erros, "\n".join(erros)
    finally:
        contexto.close()
