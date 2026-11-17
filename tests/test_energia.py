"""Testes automatizados da contribuição de energia.  Rodar: python -m pytest -q"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from energia import calculos as C          # noqa: E402
from energia import cenarios as S          # noqa: E402
from energia import parametros as P        # noqa: E402
from energia.assistente import AssistenteEnergia  # noqa: E402


# ---------- conceitos de energia e potência ----------
def test_energia_igual_potencia_vezes_tempo():
    assert C.consumo_aparelho_kwh_mes(1000, 1, 30) == pytest.approx(30)


def test_chuveiro_referencia_88_kwh():
    # 5.500 W x 32 min/dia x 30 dias = 88 kWh (mesmo valor citado pela Eletrobras/Procel)
    assert C.consumo_chuveiro_kwh_mes(5500, 4, 8) == pytest.approx(88.0)


def test_valores_negativos_sao_rejeitados():
    with pytest.raises(ValueError):
        C.consumo_aparelho_kwh_mes(-1, 1)


def test_inventario_soma_198_kwh():
    assert C.consumo_total(C.carregar_aparelhos()) == pytest.approx(197.79, abs=0.05)


# ---------- tarifa e conta ----------
def test_tarifa_com_tributos():
    assert P.TARIFA_COM_TRIBUTOS.valor == pytest.approx(0.72518 * 1.0902 * 1.2819, abs=1e-3)


def test_tarifa_social_80_kwh_gratis():
    assert C.conta_mensal(80, tarifa_social=True) == 0
    assert C.conta_mensal(100, tarifa_social=True) == pytest.approx(20 * P.TARIFA_COM_TRIBUTOS.valor, abs=0.01)


def test_custo_disponibilidade_sem_tarifa_social():
    assert C.conta_mensal(10) == pytest.approx(30 * P.TARIFA_COM_TRIBUTOS.valor, abs=0.01)


# ---------- fotovoltaica ----------
def test_geracao_um_kwp():
    # 4,632 kWh/m².dia x 0,75 x 365/12 ≈ 105,7 kWh/mês por kWp
    assert C.geracao_fv_kwh_mes(1.0) == pytest.approx(105.7, abs=0.1)


def test_fio_b_escalonamento_lei_14300():
    assert [C.fio_b_nao_compensado(a) for a in (2026, 2027, 2028, 2030)] == [0.60, 0.75, 0.90, 0.90]


def test_fv_nao_zera_a_conta():
    conta, _ = C.conta_mensal_com_fv(200, 400, 2027)
    assert conta >= 30 * P.TARIFA_COM_TRIBUTOS.valor - 0.01


def test_dimensionamento_usa_modulos_inteiros():
    kwp, mod = C.dimensionar_fv(168)
    assert mod == 3 and kwp == pytest.approx(1.65)


# ---------- comparação ----------
@pytest.mark.parametrize("ts", [True, False])
def test_comparacao_tem_renovavel_e_resultados_coerentes(ts):
    res = S.comparar(S.perfil_referencia(ts))
    assert any(r.renovavel for r in res)
    for r in res:
        assert r.investimento >= 0
        assert r.economia_ano1 > 0
        assert len(r.fluxo) == 10
    a1 = res[0]
    assert a1.payback_anos < 1          # hábitos + LED se pagam em meses


def test_payback_infinito_quando_nao_paga():
    assert math.isinf(C.payback_simples(1000, [10] * 10))


def test_pv_nao_compensa_dentro_dos_80_kwh():
    p = S.Perfil(tarifa_social=True, consumo_informado_kwh=70)
    assert S.alternativa_fotovoltaica(p).economia_ano1 == 0


# ---------- assistente ----------
@pytest.mark.parametrize("pergunta,trecho", [
    ("como economizar no chuveiro?", "chuveiro"),
    ("vale a pena colocar placa solar?", "kWp"),
    ("aquecedor solar compensa?", "aquecedor solar"),
    ("compare as alternativas", "A3"),
    ("tenho direito à tarifa social?", "80 kWh"),
    ("o que é o fio b?", "Fio B"),
    ("qual o impacto no meio ambiente?", "CO₂"),
])
def test_assistente_responde_com_fontes_e_limitacoes(pergunta, trecho):
    r = AssistenteEnergia().responder(pergunta)
    assert trecho in r
    assert "📚 Fontes" in r and "⚠️ Limitações" in r


def test_resposta_do_assistente_coerente_com_a_analise():
    a = AssistenteEnergia()
    a3 = S.alternativa_fotovoltaica(a.sessao.perfil)
    texto = a.responder("vale a pena placa solar?")
    assert f"{a3.detalhes['kwp']:.2f}".replace(".", ",") in texto


def test_fluxo_de_simulacao():
    a = AssistenteEnergia()
    a.responder("simular minha conta")
    a.responder("250")
    a.responder("não")
    r = a.responder("5 banhos de 10 minutos")
    assert "250 kWh/mês" in r and "sem Tarifa Social" in r
    assert a.sessao.perfil.banhos_dia == 5 and a.sessao.perfil.minutos_banho == 10


def test_mensagem_vazia_e_desconhecida():
    a = AssistenteEnergia()
    assert "ajuda" in a.responder("   ")
    assert "Ainda não sei" in a.responder("qual a capital da França")
