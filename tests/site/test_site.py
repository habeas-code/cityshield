"""Teste do site no navegador: as quatro abas do mapa.html sem erro no console.

Rodar da raiz do repositório:
    pip install -r tests/site/requirements.txt
    python -m playwright install --with-deps chromium
    python -m pytest -q tests/site
"""

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
