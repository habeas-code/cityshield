"""Cache em memória das respostas inteiras (#109).

Por que existe: o Neon gratuito conta o que SAI do banco, até 5 GB por mês; se
acabar, o banco fica suspenso até o mês seguinte (Neon, limites do plano
gratuito: https://neon.com/faqs/free-plan-limits-and-quotas). A camada de risco
inteira tira ~1,8 MB por chamada (1.797.535 bytes medidos na #11). As camadas só
mudam quando a carga roda (D7), então a API pode reaproveitar o mesmo texto.

Só entram respostas inteiras (sem bbox e sem filtro). Erro nunca entra: quem
pede de novo tenta o banco outra vez.

Validade de 30 minutos: é o menor valor em que o pior caso cabe nos 5 GB. Com
alguém chamando sem parar o mês todo, as três respostas (~1,88 MB juntas) saem
do banco no máximo 2 vezes por hora: 2 x 24 x 30 = 1.440 leituras x 1,88 MB =
~2,7 GB. Com 5 minutos seriam ~16 GB. Uma carga nova aparece na API em até 30
minutos, sem reiniciar; reiniciar o serviço no Render apaga o cache na hora
(docs/deploy.md).

Memória: ~1,9 MB de texto (menos de 1 % dos 512 MB do Render). A API roda num
processo só (api/Dockerfile), então há uma cópia só.
"""

import logging
import threading
import time
from collections.abc import Callable

log = logging.getLogger(__name__)

VALIDADE_SEGUNDOS = 30 * 60

# chave -> (texto, momento em que foi lido do banco)
_guardado: dict[str, tuple[str, float]] = {}
# Uma trava por chave: se dois pedidos da mesma camada chegam juntos com o
# cache vazio, o segundo espera o primeiro e reaproveita o texto, em vez de ir
# ao banco também. Camadas diferentes não se esperam: a /camadas/registros não
# fica parada atrás da /camadas/risco enquanto o Neon acorda.
_travas: dict[str, threading.Lock] = {}
# Protege só o dicionário de travas (criar a trava de uma chave nova); fica
# presa por um instante, nunca durante a consulta ao banco.
_trava_das_travas = threading.Lock()


def _trava(chave: str) -> threading.Lock:
    with _trava_das_travas:
        return _travas.setdefault(chave, threading.Lock())


def lembrar(chave: str, buscar: Callable[[], str]) -> str:
    """Devolve o texto guardado em `chave` ou, se não houver ou venceu, busca.

    Se `buscar` levantar erro (banco fora), o erro passa adiante e nada é
    guardado.
    """
    with _trava(chave):
        item = _guardado.get(chave)
        agora = time.monotonic()
        if item is not None and agora - item[1] < VALIDADE_SEGUNDOS:
            return item[0]
        texto = buscar()
        if texto is not None:
            _guardado[chave] = (texto, agora)
            log.info("cache: %s lido do banco (%d bytes)", chave, len(texto))
        return texto


def limpar() -> None:
    """Esquece tudo (usado nos testes)."""
    with _trava_das_travas:
        _guardado.clear()
        _travas.clear()
