"""Volume de água que cada solução verde segura (#17).

Cada número usa um valor publicado (docs/decisoes.md, D11) ou uma conta com o relevo, e sai
junto com a conta e a fonte, para o site mostrar. Detalhes em docs/recomendacoes.md.

    piso permeável   segura até 50 mm da chuva que cai nele        PMSP, ETS-03/2013
    jardim de chuva  lâmina de 15 cm = 150 L por m² de jardim       Hinman, WSU, 2007
    telhado verde    retém 47% da chuva (limite de baixo de 47–62%) Vacari et al., 2019
    parque           capacidade até 1 m acima do fundo, pelo relevo ANADEM
    parque (enche)   com quantos mm enche: capacidade ÷ (área de contribuição × C 0,50–0,70)  Rio-Águas, 2019

São estimativas para comparar opções e ordem de grandeza, não projeto de obra.
"""

import math

import numpy as np
from rasterio.mask import mask
from shapely.geometry import mapping

# Chuva de referência: perto da de 16/10/2026 em Sorocaba (52 mm em 24 h), quando a
# Av. Dom Aguirre e a XV de Agosto foram interditadas.
CHUVA_REF_MM = 50

PISO_CAPACIDADE_MM = 50          # brita de 25 cm × 20% de vazios
JARDIM_LAMINA_M = 0.15           # 15 cm
JARDIM_FRACAO_DA_AREA = 0.10     # premissa nossa: jardins ocupam 10% da área verde
JARDIM_AREA_QUE_ESCOA = 10       # cada m² de jardim recebe a água de 10 m² em volta (EPA 2023: jardim = 5–10% da área que drena; máx. 25:1)
TELHADO_RETENCAO = 0.47          # limite de baixo da faixa 47–62%
PARQUE_LAMINA_M = 1.0            # premissa nossa: alaga até 1 m acima do fundo
PARQUE_FORA_ABAIXO_DA_MEDIANA_M = 3   # células mais baixas que isso são lago ou leito de rio

# Parte da chuva que escorre (coeficiente de escoamento C) em "áreas de bairros":
# 0,50 a 0,70. Usamos a faixa inteira, não um número só.
ESCOAMENTO_C = (0.50, 0.70)
CHUVA_16_10_MM = 52              # chuva medida em 16/10/2026, usada para "até onde a água sobe"
CURVA_NIVEIS_M = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)   # níveis da curva cota-volume dos parques
FONTE_ESCOAMENTO = ("Prefeitura do Rio, Rio-Águas, Instruções Técnicas para Estudos Hidrológicos "
                    "e Drenagem Urbana, 2ª versão, 2019, Tabela 1")

FONTES = {
    "piso_permeavel": "Prefeitura de São Paulo, ETS-03/2013 (pavimentos permeáveis)",
    "jardim_chuva": "Hinman, Rain Gardens, WSU Extension, 2007; EPA, Bioretention Design Handbook, EPA 841-B-23-002, 2023",
    "telhado_verde": "Vacari et al., 2019, E&S Engineering and Science, UFMT",
    "parque_inundavel": "Cálculo do CityShield sobre o relevo ANADEM v1 (30 m)",
}


def _m2(valor):
    return f"{round(valor):,} m²".replace(",", ".")


def _terreno_parque(relevo, poligono_graus):
    """Alturas do terreno dentro do parque, o fundo e a área de cada célula.

    O fundo é o 10º percentil do terreno, sem as células muito abaixo da mediana (lago ou
    leito do rio, que já têm água). Relevo de 30 m: o resultado é ordem de grandeza.
    """
    try:
        recorte, _ = mask(relevo, [mapping(poligono_graus)], crop=True, filled=False)
    except ValueError:
        return None
    z = recorte[0].compressed()
    z = z[z > -100]
    if z.size == 0:
        return None
    z = z[z >= np.median(z) - PARQUE_FORA_ABAIXO_DA_MEDIANA_M]
    lat = poligono_graus.centroid.y
    celula_m2 = (relevo.res[0] * 111_320 * math.cos(math.radians(lat))) * (relevo.res[1] * 110_574)
    return z, float(np.percentile(z, 10)), celula_m2


def _volume_ate(terreno, lamina_m):
    """Volume (m³) e área alagada (m²) com a água a `lamina_m` acima do fundo."""
    z, fundo, celula_m2 = terreno
    profundidade = np.clip(fundo + lamina_m - z, 0, None)
    return float(profundidade.sum() * celula_m2), float((profundidade > 0).sum() * celula_m2)


def _curva_cota_volume(terreno):
    """Curva cota-volume: para cada nível de água, quanto o parque guarda e quanto alaga."""
    curva = []
    for lamina in CURVA_NIVEIS_M:
        volume, area = _volume_ate(terreno, lamina)
        curva.append({"nivel_m": lamina, "volume_m3": round(volume), "area_alagada_m2": round(area)})
    return curva


def _nivel_para(curva, volume_m3):
    """Nível (m) em que o parque guarda `volume_m3`, interpolando na curva. None = passa do último."""
    anterior_v, anterior_n = 0.0, 0.0
    for ponto in curva:
        if volume_m3 <= ponto["volume_m3"]:
            fracao = (volume_m3 - anterior_v) / (ponto["volume_m3"] - anterior_v)
            return anterior_n + fracao * (ponto["nivel_m"] - anterior_n)
        anterior_v, anterior_n = ponto["volume_m3"], ponto["nivel_m"]
    return None


def enchimento(capacidade_m3, contribuicao_m2, curva=None):
    """Com quantos mm de chuva o parque enche, só com a enxurrada da área em volta.

    enche com (mm) = capacidade ÷ (área de contribuição × parte que escorre) × 1000
    Sai uma faixa: o menor valor usa o C mais alto (mais água escorre, enche antes).

    Com a curva cota-volume, diz também até onde a água subiria na chuva de 16/10/2026:
    água que chega = 52 mm × área × C, e o nível sai da curva. None no fim da faixa =
    passaria do último nível da curva (a água sairia do parque).
    """
    if not capacidade_m3 or not contribuicao_m2:
        return {}
    c_min, c_max = ESCOAMENTO_C
    saida = {
        "contribuicao_m2": round(contribuicao_m2),
        "enche_com_mm": [round(capacidade_m3 / (contribuicao_m2 * c_max) * 1000),
                         round(capacidade_m3 / (contribuicao_m2 * c_min) * 1000)],
    }
    if curva:
        chega = [CHUVA_16_10_MM / 1000 * contribuicao_m2 * c for c in (c_min, c_max)]
        niveis = [_nivel_para(curva, v) for v in chega]
        saida["sobe_16_10_m"] = [round(n, 2) if n is not None else None for n in niveis]
    return saida


def estimar(p, poligono_graus, relevo):
    """Volume em m³ e a explicação, para uma área com solução já escolhida."""
    chuva_m = CHUVA_REF_MM / 1000
    area = p["area_m2"]
    solucao = p["solucao"]
    extra = {}

    if solucao == "piso_permeavel":
        chega = area * chuva_m
        volume = area * min(CHUVA_REF_MM, PISO_CAPACIDADE_MM) / 1000
        conta = f"{_m2(area)} de piso × {min(CHUVA_REF_MM, PISO_CAPACIDADE_MM)} mm (a base segura até {PISO_CAPACIDADE_MM} mm)"
        tipo = "retido"
    elif solucao == "telhado_verde":
        chega = area * chuva_m
        volume = chega * TELHADO_RETENCAO
        conta = f"{_m2(area)} de telhado × {CHUVA_REF_MM} mm × {round(TELHADO_RETENCAO * 100)}% retido"
        tipo = "retido"
    elif solucao == "jardim_chuva":
        jardim = area * JARDIM_FRACAO_DA_AREA
        chega = jardim * JARDIM_AREA_QUE_ESCOA * chuva_m
        volume = min(chega, jardim * JARDIM_LAMINA_M)
        conta = (f"jardim de {_m2(jardim)} ({round(JARDIM_FRACAO_DA_AREA * 100)}% da área) × "
                 f"{round(JARDIM_LAMINA_M * 100)} cm de lâmina")
        tipo = "retido"
    else:  # parque inundável
        terreno = _terreno_parque(relevo, poligono_graus)
        if terreno is None:
            return {}
        volume, _ = _volume_ate(terreno, PARQUE_LAMINA_M)
        extra = {"curva_cota_volume": _curva_cota_volume(terreno)}
        chega = None
        conta = f"terreno do parque até {PARQUE_LAMINA_M:g} m acima do fundo, medido no relevo"
        tipo = "capacidade"

    return {
        "volume_m3": round(volume),
        "volume_tipo": tipo,
        "fracao_retida": round(volume / chega, 2) if chega else None,
        "volume_conta": conta,
        "volume_fonte": FONTES[solucao],
        **extra,
    }
