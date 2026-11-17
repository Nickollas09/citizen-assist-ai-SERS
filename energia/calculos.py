"""
Cálculos de energia, custo, viabilidade e emissões.

Conceitos aplicados:
  Energia (kWh) = Potência (kW) x tempo (h)
  Custo (R$)    = Energia faturada (kWh) x tarifa (R$/kWh)
  Geração FV    = Potência (kWp) x irradiação (kWh/m².dia ÷ 1 kW/m²) x PR x dias
  Emissões      = Energia (kWh) x fator de emissão (kgCO2/kWh)
"""

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

from . import parametros as P

RAIZ = Path(__file__).resolve().parent.parent
ARQ_APARELHOS = RAIZ / "dados" / "aparelhos_familia_referencia.csv"


# ---------------------------------------------------------------------------
# Consumo
# ---------------------------------------------------------------------------
def consumo_aparelho_kwh_mes(potencia_w, horas_dia, dias_mes=30, quantidade=1):
    """E = P x t. Retorna kWh/mês."""
    if potencia_w < 0 or horas_dia < 0 or dias_mes < 0 or quantidade < 0:
        raise ValueError("valores não podem ser negativos")
    return quantidade * (potencia_w / 1000.0) * horas_dia * dias_mes


def consumo_chuveiro_kwh_mes(potencia_w=5500, banhos_dia=4, minutos_banho=8, dias=30):
    return consumo_aparelho_kwh_mes(potencia_w, banhos_dia * minutos_banho / 60.0, dias)


def carregar_aparelhos(caminho=ARQ_APARELHOS):
    """Lê o inventário de aparelhos e calcula o kWh/mês de cada linha."""
    itens = []
    with open(caminho, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            qtd = float(linha["quantidade"] or 1)
            if linha["consumo_fixo_kwh_mes"]:
                kwh = float(linha["consumo_fixo_kwh_mes"]) * qtd
            else:
                kwh = consumo_aparelho_kwh_mes(
                    float(linha["potencia_w"]), float(linha["uso_horas_dia"]),
                    float(linha["dias_mes"]), qtd)
            itens.append({**linha, "kwh_mes": round(kwh, 2)})
    return itens


def consumo_total(itens):
    return round(sum(i["kwh_mes"] for i in itens), 2)


# ---------------------------------------------------------------------------
# Conta de luz
# ---------------------------------------------------------------------------
def kwh_faturados(consumo_kwh, tarifa_social=False):
    """Energia que efetivamente é cobrada no mês (sem geração própria)."""
    if consumo_kwh < 0:
        raise ValueError("consumo negativo")
    if tarifa_social:
        return max(0.0, consumo_kwh - P.TSEE_FAIXA_GRATUITA.valor)
    return max(consumo_kwh, P.CUSTO_DISPONIBILIDADE_MONOFASICO.valor)


def conta_mensal(consumo_kwh, tarifa_social=False, tarifa=None):
    """Valor da energia na fatura (R$/mês), sem bandeira e sem iluminação pública."""
    tarifa = P.TARIFA_COM_TRIBUTOS.valor if tarifa is None else tarifa
    return round(kwh_faturados(consumo_kwh, tarifa_social) * tarifa, 2)


def valor_kwh_economizado(consumo_kwh, tarifa_social=False):
    """Quanto vale, em R$, cada kWh a menos na faixa atual de consumo (tarifa marginal)."""
    return conta_mensal(consumo_kwh, tarifa_social) - conta_mensal(max(consumo_kwh - 1, 0), tarifa_social)


# ---------------------------------------------------------------------------
# Fotovoltaico
# ---------------------------------------------------------------------------
def geracao_fv_kwh_mes(kwp, irradiacao=None, pr=None, ano_operacao=1):
    irradiacao = P.IRRADIACAO_PLANO_INCLINADO.valor if irradiacao is None else irradiacao
    pr = P.PERFORMANCE_RATIO.valor if pr is None else pr
    degr = (1 - P.DEGRADACAO_ANUAL_FV.valor) ** (ano_operacao - 1)
    return kwp * irradiacao * pr * 365 / 12 * degr


def dimensionar_fv(consumo_alvo_kwh_mes, irradiacao=None, pr=None):
    """kWp necessário para gerar o consumo-alvo, arredondado para módulos inteiros."""
    if consumo_alvo_kwh_mes <= 0:
        return 0.0, 0
    kwp_ideal = consumo_alvo_kwh_mes / geracao_fv_kwh_mes(1.0, irradiacao, pr)
    # arredonda para o número inteiro de módulos mais próximo (mínimo 1):
    # arredondar sempre para cima gera créditos que a família não consegue usar
    modulos = max(1, round(kwp_ideal * 1000 / P.POTENCIA_MODULO.valor))
    return modulos * P.POTENCIA_MODULO.valor / 1000, modulos


def fio_b_nao_compensado(ano):
    if ano in P.FIO_B_NAO_COMPENSADO:
        return P.FIO_B_NAO_COMPENSADO[ano]
    if ano < 2026:
        return 0.45
    return P.FIO_B_APOS_2028.valor


def conta_mensal_com_fv(consumo_kwh, geracao_kwh, ano, tarifa_social=False, tarifa=None):
    """
    Fatura com micro geração (Lei 14.300), modelo simplificado mensal:
      - parte da geração é consumida na hora (simultaneidade);
      - o restante é injetado e compensa o consumo da rede;
      - sobre cada kWh compensado paga-se a fração não compensada do Fio B;
      - sem Tarifa Social: valor mínimo = custo de disponibilidade (30 kWh);
      - com Tarifa Social: 80 kWh gratuitos aplicados ao consumo líquido
        (interação TSEE x GD deve ser confirmada com a distribuidora).
    """
    tarifa = P.TARIFA_COM_TRIBUTOS.valor if tarifa is None else tarifa
    autoconsumo = min(geracao_kwh * P.SIMULTANEIDADE_FV.valor, consumo_kwh)
    injetado = geracao_kwh - autoconsumo
    da_rede = consumo_kwh - autoconsumo
    liquido_antes_ts = da_rede
    if tarifa_social:
        # só vale a pena compensar o que seria cobrado (acima de 80 kWh)
        cobravel = max(0.0, da_rede - P.TSEE_FAIXA_GRATUITA.valor)
        compensado = min(injetado, cobravel)
        energia = (cobravel - compensado) * tarifa
        minimo = 0.0
    else:
        compensado = min(injetado, liquido_antes_ts)
        energia = (liquido_antes_ts - compensado) * tarifa
        minimo = P.CUSTO_DISPONIBILIDADE_MONOFASICO.valor * tarifa
    custo_fio_b = compensado * P.FIO_B_SEM_TRIBUTOS.valor * P.FATOR_TRIBUTOS.valor * fio_b_nao_compensado(ano)
    # ANEEL: paga-se o maior entre (consumo líquido + Fio B) e o custo de disponibilidade
    return round(max(energia + custo_fio_b, minimo), 2), {
        "autoconsumo_kwh": round(autoconsumo, 1),
        "injetado_kwh": round(injetado, 1),
        "compensado_kwh": round(compensado, 1),
        "sobra_creditos_kwh": round(injetado - compensado, 1),
        "custo_fio_b": round(custo_fio_b, 2),
    }


# ---------------------------------------------------------------------------
# Indicadores financeiros e ambientais
# ---------------------------------------------------------------------------
@dataclass
class Resultado:
    nome: str
    renovavel: bool
    investimento: float
    kwh_economizados_mes: float          # energia da rede evitada (média ano 1)
    economia_ano1: float                 # R$/ano
    fluxo: list = field(default_factory=list)   # economia líquida por ano (R$)
    payback_anos: float = math.inf
    vpl: float = 0.0
    economia_acumulada: float = 0.0
    co2_evitado_kg_ano: float = 0.0
    detalhes: dict = field(default_factory=dict)


def payback_simples(investimento, fluxo):
    if investimento <= 0:
        return 0.0
    acumulado = 0.0
    for i, valor in enumerate(fluxo):
        if valor > 0 and acumulado + valor >= investimento:
            return round(i + (investimento - acumulado) / valor, 2)
        acumulado += valor
    return math.inf


def vpl(investimento, fluxo, taxa=None):
    taxa = P.TAXA_DESCONTO_REAL.valor if taxa is None else taxa
    return round(-investimento + sum(v / (1 + taxa) ** (i + 1) for i, v in enumerate(fluxo)), 2)


def co2_kg(kwh, fator=None):
    fator = P.FATOR_EMISSAO_SIN.valor if fator is None else fator
    return kwh * fator


def fechar_resultado(r: Resultado):
    r.payback_anos = payback_simples(r.investimento, r.fluxo)
    r.vpl = vpl(r.investimento, r.fluxo)
    r.economia_acumulada = round(sum(r.fluxo) - r.investimento, 2)
    return r
