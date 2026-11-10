"""Leitura e validação do bbox: o retângulo da área visível do mapa.

Formato: "xmin,ymin,xmax,ymax" em lon/lat (SRID 4326), na ordem
oeste, sul, leste, norte. Exemplo (área piloto):
"-47.455,-23.478,-47.439,-23.463".
"""

ORDEM = "use xmin,ymin,xmax,ymax (oeste,sul,leste,norte) em graus"


class BboxInvalido(ValueError):
    """O texto não é um retângulo válido. A mensagem diz o motivo."""


def ler_bbox(texto: str) -> tuple[float, float, float, float]:
    partes = [p.strip() for p in texto.split(",")]
    if len(partes) != 4:
        raise BboxInvalido(f"bbox precisa de 4 números e veio com {len(partes)}: {ORDEM}.")
    try:
        xmin, ymin, xmax, ymax = (float(p) for p in partes)
    except ValueError:
        raise BboxInvalido(f"bbox só aceita números: {ORDEM}.") from None

    # As comparações também recusam "nan" e "inf", que o float() aceita.
    if not all(-180 <= x <= 180 for x in (xmin, xmax)):
        raise BboxInvalido("longitude do bbox fora de -180 a 180.")
    if not all(-90 <= y <= 90 for y in (ymin, ymax)):
        raise BboxInvalido("latitude do bbox fora de -90 a 90.")
    if not xmin < xmax:
        raise BboxInvalido(f"no bbox, xmin tem que ser menor que xmax: {ORDEM}.")
    if not ymin < ymax:
        raise BboxInvalido(f"no bbox, ymin tem que ser menor que ymax: {ORDEM}.")
    return xmin, ymin, xmax, ymax
