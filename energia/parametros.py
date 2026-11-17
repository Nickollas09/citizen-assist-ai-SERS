"""
Parâmetros técnicos e econômicos usados na análise de energia do Citizen Assist AI.

Contribuição da disciplina: Soluções em Energias Renováveis e Sustentáveis (SERS).

Regra do projeto: TODO número usado nos cálculos está aqui, com
  - valor e unidade,
  - tipo: "real/público" (dado publicado) ou "estimado" (premissa justificada),
  - fonte (id que aponta para docs/05_referencias.md).

Período de referência da análise: 12 meses (1 ano), com tarifas vigentes
após o reajuste da Enel SP de 04/07/2026. Horizonte financeiro: 10 anos.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Parametro:
    valor: float
    unidade: str
    tipo: str          # "real/público" ou "estimado"
    fonte: str         # id da referência (ver FONTES e docs/05_referencias.md)
    nota: str = ""


# ---------------------------------------------------------------------------
# 1. Tarifa de energia (Enel Distribuição São Paulo, grupo B1 residencial)
# ---------------------------------------------------------------------------
# TE + TUSD sem tributos em vigor de jul/2025 a jul/2026, lido em fatura B1
# pública (TE 0,29274 + TUSD 0,43244 = 0,72518 R$/kWh), igual aos R$ 725,18/MWh
# divulgados no reajuste de 2025.
TARIFA_SEM_TRIBUTOS_2025 = Parametro(
    0.72518, "R$/kWh", "real/público", "R1",
    "TE 0,29274 + TUSD 0,43244 (B1 Enel SP, jul/2025-jul/2026)")

# Reajuste residencial aprovado pela ANEEL para a Enel SP a partir de 04/07/2026.
REAJUSTE_RESIDENCIAL_2026 = Parametro(
    0.0902, "fração", "real/público", "R2", "efeito médio residencial B1")

# Fator de tributos (ICMS 18% + PIS/COFINS) obtido da mesma fatura:
# preço com tributos 0,92964 / preço sem tributos 0,72518.
FATOR_TRIBUTOS = Parametro(
    1.2819, "adimensional", "real/público", "R1",
    "PIS/COFINS variam mês a mês; regras de ICMS para baixa renda não modeladas")

TARIFA_SEM_TRIBUTOS = Parametro(
    round(TARIFA_SEM_TRIBUTOS_2025.valor * (1 + REAJUSTE_RESIDENCIAL_2026.valor), 4),
    "R$/kWh", "estimado", "R1,R2",
    "tarifa 2025 x (1 + reajuste residencial 2026)")

TARIFA_COM_TRIBUTOS = Parametro(
    round(TARIFA_SEM_TRIBUTOS.valor * FATOR_TRIBUTOS.valor, 4),
    "R$/kWh", "estimado", "R1,R2",
    "bandeira verde; não inclui bandeiras nem contribuição de iluminação pública")

# ---------------------------------------------------------------------------
# 2. Tarifa Social de Energia Elétrica (TSEE) - Lei 15.235/2025
# ---------------------------------------------------------------------------
TSEE_FAIXA_GRATUITA = Parametro(
    80, "kWh/mês", "real/público", "R3",
    "famílias CadÚnico com renda per capita até 1/2 salário mínimo e BPC; "
    "o que passa de 80 kWh é cobrado pela tarifa normal")

# ---------------------------------------------------------------------------
# 3. Geração distribuída (Lei 14.300/2022)
# ---------------------------------------------------------------------------
CUSTO_DISPONIBILIDADE_MONOFASICO = Parametro(
    30, "kWh/mês", "real/público", "R4", "bifásico 50 kWh; trifásico 100 kWh")

# Percentual do Fio B NÃO compensado, por ano (art. 27 da Lei 14.300).
FIO_B_NAO_COMPENSADO = {2026: 0.60, 2027: 0.75, 2028: 0.90}
FIO_B_APOS_2028 = Parametro(
    0.90, "fração", "estimado", "R4",
    "regra após 2028 ainda não definida pela ANEEL; mantido 90% (conservador)")

FIO_B_SEM_TRIBUTOS = Parametro(
    0.22, "R$/kWh", "estimado", "R5,R6",
    "valor exato da TUSD Fio B da Enel SP não localizado; estimado entre o "
    "Fio B da CPFL Paulista (~0,21 R$/kWh) e a parcela de distribuição na "
    "tarifa média nacional (~31%)")

# ---------------------------------------------------------------------------
# 4. Recurso solar e sistema fotovoltaico
# ---------------------------------------------------------------------------
IRRADIACAO_PLANO_INCLINADO = Parametro(
    4.632, "kWh/m².dia", "real/público", "R7",
    "Mogi das Cruzes (RMSP), plano inclinado; usado como aproximação para a "
    "capital. Refinar com o CRESESB SunData pelo CEP do usuário")

PERFORMANCE_RATIO = Parametro(
    0.75, "adimensional", "estimado", "R7",
    "perdas por temperatura, sujeira, cabos e inversor (valor didático usual)")

DEGRADACAO_ANUAL_FV = Parametro(0.005, "fração/ano", "estimado", "R8")

PRECO_FV_POR_WP = Parametro(
    3.40, "R$/Wp", "estimado", "R9,R10",
    "sistemas pequenos (1-2 kWp) custam mais por Wp que a média nacional; "
    "faixa de sensibilidade 2,45 (média nacional 1T2026) a 4,20 R$/Wp")
PRECO_FV_POR_WP_MIN = Parametro(2.45, "R$/Wp", "real/público", "R9")
PRECO_FV_POR_WP_MAX = Parametro(4.20, "R$/Wp", "real/público", "R10")

SIMULTANEIDADE_FV = Parametro(
    0.30, "fração", "estimado", "R11",
    "parte da geração consumida na hora; família fora de casa de dia")

POTENCIA_MODULO = Parametro(550, "Wp", "estimado", "R9", "módulo comercial comum")

# ---------------------------------------------------------------------------
# 5. Aquecimento solar de água
# ---------------------------------------------------------------------------
CUSTO_AQUECEDOR_SOLAR = Parametro(
    5000, "R$", "estimado", "R12,R13",
    "200 L + 2 coletores (~3 m²). Estudo de caso: R$ 4.180 instalado; "
    "faixa de mercado para sistemas completos chega a R$ 7.000 ou mais")
CUSTO_AQUECEDOR_SOLAR_MIN = Parametro(4180, "R$", "real/público", "R12")
CUSTO_AQUECEDOR_SOLAR_MAX = Parametro(7000, "R$", "real/público", "R13")

FRACAO_SOLAR = Parametro(
    0.65, "fração", "estimado", "R13",
    "parte da energia de aquecimento suprida pelo sol no ano; o chuveiro "
    "continua como apoio em dias nublados e no inverno")

MANUTENCAO_AQUECEDOR = Parametro(
    120, "R$/ano", "estimado", "R13", "limpeza de coletores e revisão de válvulas")

# ---------------------------------------------------------------------------
# 6. Emissões
# ---------------------------------------------------------------------------
FATOR_EMISSAO_SIN = Parametro(
    0.0599, "kgCO2eq/kWh", "real/público", "R14",
    "setor elétrico brasileiro, ano-base 2024 (BEN 2025)")
FATOR_EMISSAO_SIN_MIN = Parametro(
    0.0289, "kgCO2/kWh", "real/público", "R15",
    "fator médio mensal do SIN em abr/2025 (MCTI/SIRENE)")
EMISSAO_CICLO_VIDA_FV = Parametro(
    0.041, "kgCO2eq/kWh", "real/público", "R16",
    "mediana do ciclo de vida de FV em telhado (IPCC AR5)")

# ---------------------------------------------------------------------------
# 7. Premissas financeiras
# ---------------------------------------------------------------------------
HORIZONTE_ANOS = Parametro(10, "anos", "estimado", "-", "vida útil > 20 anos; horizonte prudente")
TAXA_DESCONTO_REAL = Parametro(
    0.06, "fração/ano", "estimado", "-",
    "custo de oportunidade real (ex.: aplicação conservadora)")
REAJUSTE_REAL_TARIFA = Parametro(
    0.0, "fração/ano", "estimado", "R2",
    "cenário base em valores reais constantes; sensibilidade com +3%/ano")
ANO_INSTALACAO = 2027

# ---------------------------------------------------------------------------
# Fontes (resumo; versão completa em docs/05_referencias.md)
# ---------------------------------------------------------------------------
FONTES = {
    "R1": "Fatura B1 Enel SP (TE/TUSD e tributos, 2026) e Exame 01/07/2025 - tarifa B1 R$ 725,18/MWh",
    "R2": "ANEEL - Reajuste Tarifário Enel SP 2026 (+9,02% residencial, vigência 04/07/2026)",
    "R3": "Lei 15.235/2025 e ANEEL - Tarifa Social: gratuidade até 80 kWh/mês",
    "R4": "Lei 14.300/2022 (art. 27) e REN ANEEL 1.059/2023 - Fio B e custo de disponibilidade",
    "R5": "Canal Solar (02/01/2026) - 60% do Fio B em 2026; exemplo CPFL Paulista",
    "R6": "ANEEL infoTarifa mar/2026 - composição média da tarifa B1",
    "R7": "USP/IEE - exemplo de dimensionamento FV em Mogi das Cruzes (Atlas Brasileiro de Energia Solar/LABREN)",
    "R8": "Garantias usuais de fabricantes de módulos (degradação ~0,5%/ano)",
    "R9": "Solfácil via Cenário Energia (09/06/2026) - preço médio nacional R$ 2,45/Wp",
    "R10": "Estado de Minas/UAI (19/10/2026) - faixa R$ 3.400-4.200/kWp residencial",
    "R11": "Premissa da equipe para família ausente durante o dia",
    "R12": "UFRJ Macaé via Click Petróleo e Gás (19/05/2026) - sistema 200 L, R$ 4.180",
    "R13": "Idec e Monitor do Mercado (2026) - aquecimento solar de água, custos e dimensionamento",
    "R14": "EPE - Balanço Energético Nacional 2025 (ano-base 2024): 59,9 kgCO2eq/MWh",
    "R15": "MCTI/SIRENE - fatores médios de emissão do SIN 2025",
    "R16": "IPCC AR5 WGIII, Anexo III - emissões de ciclo de vida",
    "R17": "Idec / Eletrobras-Procel - consumo médio de eletrodomésticos",
    "R18": "Eletrobras/Procel - Pesquisa de Posse e Hábitos (chuveiro ~24% do consumo residencial)",
    "R19": "EPE (2023) - consumo per capita por faixa de renda",
}


def tabela_parametros():
    """Lista (nome, Parametro) de todos os parâmetros, para exportar e documentar."""
    return [(nome, valor) for nome, valor in globals().items()
            if isinstance(valor, Parametro)]
