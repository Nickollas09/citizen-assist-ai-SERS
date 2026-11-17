"""
Perfis de família e comparação das alternativas para a MESMA necessidade
(energia elétrica de um domicílio de 4 pessoas atendido pela Enel SP)
no MESMO período de referência (12 meses; fluxo financeiro em 10 anos).

Alternativas:
  A1 - Eficiência energética e hábitos (LED, banho mais curto, posição verão,
       cuidados com a geladeira, standby). Não renovável, custo muito baixo.
  A2 - Aquecedor solar de água (fonte RENOVÁVEL térmica) substituindo parte
       do chuveiro elétrico.
  A3 - Sistema fotovoltaico conectado à rede (fonte RENOVÁVEL elétrica,
       micro geração distribuída pela Lei 14.300).
  A1+A2 - combinação recomendada para quem tem condições de investir.
"""

from dataclasses import dataclass

from . import calculos as C
from . import parametros as P

POTENCIA_VERAO_W = 3200     # estimado: posição "verão" típica de chuveiros 5.500 W
MESES_VERAO = 6             # estimado: out-mar
CUSTO_LED_UN = 12.0         # estimado: preço de varejo de lâmpada LED 9 W (R$)
POTENCIA_LED_W = 9
REDUCAO_GELADEIRA = 0.10    # estimado: vedação, distância da parede, porta fechada
REDUCAO_STANDBY_KWH = 3.0   # estimado: desligar da tomada TV/carregadores


@dataclass
class Perfil:
    nome: str = "Família de referência"
    tarifa_social: bool = True
    pessoas: int = 4
    banhos_dia: int = 4
    minutos_banho: float = 8
    potencia_chuveiro_w: float = 5500
    lampadas_incandescentes: int = 2       # 60 W, 3 h/dia
    lampadas_fluorescentes: int = 4        # 15 W, 5 h/dia
    geladeira_kwh_mes: float = 55.0
    outros_kwh_mes: float = 0.0            # preenchido a partir do inventário
    consumo_informado_kwh: float | None = None   # se o usuário souber o da conta

    @property
    def chuveiro_kwh(self):
        return C.consumo_chuveiro_kwh_mes(self.potencia_chuveiro_w, self.banhos_dia, self.minutos_banho)

    @property
    def iluminacao_kwh(self):
        return (C.consumo_aparelho_kwh_mes(60, 3, 30, self.lampadas_incandescentes)
                + C.consumo_aparelho_kwh_mes(15, 5, 30, self.lampadas_fluorescentes))

    @property
    def consumo_kwh(self):
        if self.consumo_informado_kwh is not None:
            return self.consumo_informado_kwh
        return round(self.chuveiro_kwh + self.iluminacao_kwh + self.geladeira_kwh_mes + self.outros_kwh_mes, 2)


def perfil_referencia(tarifa_social=True):
    """Perfil montado a partir de dados/aparelhos_familia_referencia.csv."""
    itens = C.carregar_aparelhos()
    total = C.consumo_total(itens)
    p = Perfil(nome="Família A (com Tarifa Social)" if tarifa_social else "Família B (sem Tarifa Social)",
               tarifa_social=tarifa_social)
    p.outros_kwh_mes = round(total - p.chuveiro_kwh - p.iluminacao_kwh - p.geladeira_kwh_mes, 2)
    return p


# ---------------------------------------------------------------------------
def _fluxo_constante(economia_ano, anos=None, custo_anual=0.0, reajuste=None):
    anos = int(P.HORIZONTE_ANOS.valor) if anos is None else anos
    reajuste = P.REAJUSTE_REAL_TARIFA.valor if reajuste is None else reajuste
    return [round(economia_ano * (1 + reajuste) ** i - custo_anual, 2) for i in range(anos)]


def _economia_reais_mes(perfil, kwh_a_menos):
    antes = C.conta_mensal(perfil.consumo_kwh, perfil.tarifa_social)
    depois = C.conta_mensal(max(perfil.consumo_kwh - kwh_a_menos, 0), perfil.tarifa_social)
    return antes - depois


def economia_habitos_kwh(perfil, minutos_meta=None):
    """Detalha a redução de A1, item a item (kWh/mês)."""
    minutos_meta = max(5, perfil.minutos_banho - 2) if minutos_meta is None else minutos_meta
    minutos_meta = min(minutos_meta, perfil.minutos_banho)
    ch_antes = perfil.chuveiro_kwh
    inverno = C.consumo_chuveiro_kwh_mes(perfil.potencia_chuveiro_w, perfil.banhos_dia, minutos_meta)
    verao = C.consumo_chuveiro_kwh_mes(min(POTENCIA_VERAO_W, perfil.potencia_chuveiro_w), perfil.banhos_dia, minutos_meta)
    ch_depois = (inverno * (12 - MESES_VERAO) + verao * MESES_VERAO) / 12
    led = (perfil.lampadas_incandescentes * C.consumo_aparelho_kwh_mes(60 - POTENCIA_LED_W, 3)
           + perfil.lampadas_fluorescentes * C.consumo_aparelho_kwh_mes(15 - POTENCIA_LED_W, 5))
    itens = {
        "chuveiro (banho %.0f→%.0f min + posição verão %d meses)" % (perfil.minutos_banho, minutos_meta, MESES_VERAO): ch_antes - ch_depois,
        "troca de %d lâmpadas por LED 9 W" % (perfil.lampadas_incandescentes + perfil.lampadas_fluorescentes): led,
        "geladeira (vedação, ventilação, porta fechada)": perfil.geladeira_kwh_mes * REDUCAO_GELADEIRA,
        "standby e carregadores": REDUCAO_STANDBY_KWH,
    }
    return {k: round(v, 2) for k, v in itens.items()}, ch_depois


def alternativa_eficiencia(perfil, reajuste=None, adesao=1.0):
    itens, _ = economia_habitos_kwh(perfil)
    kwh = sum(itens.values()) * adesao
    invest = (perfil.lampadas_incandescentes + perfil.lampadas_fluorescentes) * CUSTO_LED_UN
    eco_ano = _economia_reais_mes(perfil, kwh) * 12
    r = C.Resultado("A1 · Eficiência e hábitos", False, invest, round(kwh, 1), round(eco_ano, 2),
                    _fluxo_constante(eco_ano, reajuste=reajuste),
                    co2_evitado_kg_ano=round(C.co2_kg(kwh * 12), 1),
                    detalhes={"itens_kwh_mes": itens, "adesao": adesao})
    return C.fechar_resultado(r)


def alternativa_aquecedor_solar(perfil, custo=None, reajuste=None, chuveiro_kwh=None, nome=None):
    custo = P.CUSTO_AQUECEDOR_SOLAR.valor if custo is None else custo
    base = perfil.chuveiro_kwh if chuveiro_kwh is None else chuveiro_kwh
    kwh = base * P.FRACAO_SOLAR.valor
    eco_ano = _economia_reais_mes(perfil, kwh) * 12
    r = C.Resultado(nome or "A2 · Aquecedor solar de água", True, custo, round(kwh, 1), round(eco_ano, 2),
                    _fluxo_constante(eco_ano, custo_anual=P.MANUTENCAO_AQUECEDOR.valor, reajuste=reajuste),
                    co2_evitado_kg_ano=round(C.co2_kg(kwh * 12), 1),
                    detalhes={"chuveiro_kwh_mes": round(base, 1), "fracao_solar": P.FRACAO_SOLAR.valor})
    return C.fechar_resultado(r)


def alternativa_fotovoltaica(perfil, preco_wp=None, reajuste=None, fator_emissao=None):
    preco_wp = P.PRECO_FV_POR_WP.valor if preco_wp is None else preco_wp
    reajuste = P.REAJUSTE_REAL_TARIFA.valor if reajuste is None else reajuste
    piso = P.TSEE_FAIXA_GRATUITA.valor if perfil.tarifa_social else P.CUSTO_DISPONIBILIDADE_MONOFASICO.valor
    alvo = max(perfil.consumo_kwh - piso, 0)
    # a parte consumida na hora não paga Fio B; dimensiona-se para o consumo-alvo
    kwp, modulos = C.dimensionar_fv(alvo)
    invest = round(kwp * 1000 * preco_wp, 2)
    sem = C.conta_mensal(perfil.consumo_kwh, perfil.tarifa_social)
    fluxo, contas = [], []
    for i in range(int(P.HORIZONTE_ANOS.valor)):
        ano = P.ANO_INSTALACAO + i
        ger = C.geracao_fv_kwh_mes(kwp, ano_operacao=i + 1)
        com, det = C.conta_mensal_com_fv(perfil.consumo_kwh, ger, ano, perfil.tarifa_social)
        fluxo.append(round((sem - com) * 12 * (1 + reajuste) ** i, 2))
        contas.append((ano, round(ger, 1), com, det))
    ger1 = contas[0][1]
    det1 = contas[0][3]
    evitado = det1["autoconsumo_kwh"] + det1["compensado_kwh"]   # energia da rede efetivamente abatida
    fator = (P.FATOR_EMISSAO_SIN.valor if fator_emissao is None else fator_emissao) - P.EMISSAO_CICLO_VIDA_FV.valor
    r = C.Resultado("A3 · Solar fotovoltaica", True, invest, round(evitado, 1), fluxo[0], fluxo,
                    co2_evitado_kg_ano=round(ger1 * 12 * fator, 1),
                    detalhes={"kwp": kwp, "geracao_kwh_mes": ger1, "modulos": modulos, "alvo_kwh_mes": round(alvo, 1),
                              "conta_sem_fv": sem, "contas_por_ano": contas, "area_m2": round(modulos * 2.6, 1)})
    return C.fechar_resultado(r)


def alternativa_combinada(perfil, reajuste=None):
    a1 = alternativa_eficiencia(perfil, reajuste)
    _, ch_depois = economia_habitos_kwh(perfil)
    kwh = a1.kwh_economizados_mes + ch_depois * P.FRACAO_SOLAR.valor
    invest = a1.investimento + P.CUSTO_AQUECEDOR_SOLAR.valor
    eco_ano = _economia_reais_mes(perfil, kwh) * 12
    r = C.Resultado("A1+A2 · Hábitos + aquecedor solar", True, invest, round(kwh, 1), round(eco_ano, 2),
                    _fluxo_constante(eco_ano, custo_anual=P.MANUTENCAO_AQUECEDOR.valor, reajuste=reajuste),
                    co2_evitado_kg_ano=round(C.co2_kg(kwh * 12), 1))
    return C.fechar_resultado(r)


def comparar(perfil, reajuste=None):
    return [alternativa_eficiencia(perfil, reajuste),
            alternativa_aquecedor_solar(perfil, reajuste=reajuste),
            alternativa_fotovoltaica(perfil, reajuste=reajuste),
            alternativa_combinada(perfil, reajuste)]


def sensibilidade(perfil):
    """Como os resultados mudam quando as premissas incertas variam."""
    linhas = []
    base = {r.nome: r for r in comparar(perfil)}
    def add(cenario, r):
        linhas.append({"cenario": cenario, "alternativa": r.nome, "investimento": r.investimento,
                       "economia_ano1": r.economia_ano1, "payback_anos": r.payback_anos, "vpl_10a": r.vpl})
    for r in base.values():
        add("base", r)
    add("A1 com só 50% de adesão aos hábitos", alternativa_eficiencia(perfil, adesao=0.5))
    add("A2 custo mínimo (R$ 4.180)", alternativa_aquecedor_solar(perfil, custo=P.CUSTO_AQUECEDOR_SOLAR_MIN.valor))
    add("A2 custo alto (R$ 7.000)", alternativa_aquecedor_solar(perfil, custo=P.CUSTO_AQUECEDOR_SOLAR_MAX.valor))
    add("A3 preço 2,45 R$/Wp", alternativa_fotovoltaica(perfil, preco_wp=P.PRECO_FV_POR_WP_MIN.valor))
    add("A3 preço 4,20 R$/Wp", alternativa_fotovoltaica(perfil, preco_wp=P.PRECO_FV_POR_WP_MAX.valor))
    add("A2 tarifa +3%/ano real", alternativa_aquecedor_solar(perfil, reajuste=0.03))
    add("A3 tarifa +3%/ano real", alternativa_fotovoltaica(perfil, reajuste=0.03))
    return linhas
