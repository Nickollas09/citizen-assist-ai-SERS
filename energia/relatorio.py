"""
Gera as tabelas (CSV) e gráficos (PNG) da análise em resultados/.

Uso:
    python -m energia.relatorio
"""

import csv
from pathlib import Path

from . import calculos as C
from . import cenarios as S
from . import parametros as P

SAIDA = C.RAIZ / "resultados"
GRAF = SAIDA / "graficos"

# paleta categórica de referência (validada para daltonismo), modo claro
COR = {"s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a", "s4": "#6250d6",
       "texto": "#0b0b0b", "texto2": "#52514e", "grade": "#e4e3df", "fundo": "#fcfcfb"}


def _csv(nome, linhas, campos=None):
    caminho = SAIDA / nome
    campos = campos or list(linhas[0].keys())
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)
    return caminho


def tabelas():
    SAIDA.mkdir(exist_ok=True)
    # 1) parâmetros com origem
    _csv("parametros_utilizados.csv", [
        {"parametro": n, "valor": p.valor, "unidade": p.unidade, "tipo": p.tipo,
         "fonte": p.fonte, "nota": p.nota} for n, p in P.tabela_parametros()])
    # 2) consumo por aparelho
    itens = C.carregar_aparelhos()
    total = C.consumo_total(itens)
    _csv("consumo_por_aparelho.csv", [
        {"aparelho": i["aparelho"], "kwh_mes": i["kwh_mes"],
         "participacao_pct": round(100 * i["kwh_mes"] / total, 1), "tipo_dado": i["tipo_dado"],
         "fonte": i["fonte"]} for i in itens] + [{"aparelho": "TOTAL", "kwh_mes": total, "participacao_pct": 100}])
    # 3) comparação, fluxos e sensibilidade para as duas famílias
    comp, fluxos, sens = [], [], []
    for ts in (True, False):
        p = S.perfil_referencia(ts)
        conta0 = C.conta_mensal(p.consumo_kwh, ts)
        for r in S.comparar(p):
            comp.append({"familia": p.nome, "alternativa": r.nome, "renovavel": "sim" if r.renovavel else "não",
                         "consumo_base_kwh_mes": p.consumo_kwh, "conta_base_rs_mes": conta0,
                         "kwh_rede_evitados_mes": r.kwh_economizados_mes,
                         "investimento_rs": r.investimento, "economia_ano1_rs": r.economia_ano1,
                         "conta_apos_rs_mes": round(conta0 - r.economia_ano1 / 12, 2),
                         "payback_anos": r.payback_anos, "vpl_10a_6pct_rs": r.vpl,
                         "saldo_10a_rs": r.economia_acumulada, "co2_evitado_kg_ano": r.co2_evitado_kg_ano})
            acum = -r.investimento
            fluxos.append({"familia": p.nome, "alternativa": r.nome, "ano": 0, "fluxo_rs": -r.investimento, "acumulado_rs": acum})
            for i, v in enumerate(r.fluxo, start=1):
                acum += v
                fluxos.append({"familia": p.nome, "alternativa": r.nome, "ano": i, "fluxo_rs": v, "acumulado_rs": round(acum, 2)})
        for linha in S.sensibilidade(p):
            sens.append({"familia": p.nome, **linha})
        _csv(f"fotovoltaica_ano_a_ano_{'familia_A' if ts else 'familia_B'}.csv", [
            {"ano": ano, "geracao_kwh_mes": g, "conta_com_fv_rs_mes": conta, **det}
            for ano, g, conta, det in S.alternativa_fotovoltaica(p).detalhes["contas_por_ano"]])
    _csv("comparacao_alternativas.csv", comp)
    _csv("fluxo_caixa_10anos.csv", fluxos)
    _csv("sensibilidade.csv", sens)
    return comp, fluxos, itens


def graficos(comp, fluxos, itens):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib não instalado: gráficos não gerados (as tabelas CSV foram geradas).")
        return
    GRAF.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.edgecolor": COR["grade"], "axes.labelcolor": COR["texto2"],
                         "xtick.color": COR["texto2"], "ytick.color": COR["texto2"],
                         "figure.facecolor": COR["fundo"], "axes.facecolor": COR["fundo"]})

    def estilo(ax):
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
        ax.grid(axis="x" if ax.get_ylabel() == "" else "y", color=COR["grade"], linewidth=0.8)
        ax.set_axisbelow(True)

    # 1) consumo por aparelho
    dados = sorted(itens, key=lambda i: i["kwh_mes"])
    fig, ax = plt.subplots(figsize=(8, 4.6))
    nomes = [i["aparelho"].split("(")[0].strip() for i in dados]
    vals = [i["kwh_mes"] for i in dados]
    ax.barh(nomes, vals, color=COR["s1"], height=0.6)
    total = sum(vals)
    for y, v in enumerate(vals):
        ax.text(v + 1, y, f"{v:.0f} kWh ({100 * v / total:.0f}%)", va="center", fontsize=9, color=COR["texto2"])
    ax.set_xlim(0, max(vals) * 1.35)
    ax.set_xlabel("kWh por mês")
    fig.suptitle(f"Consumo estimado da família de referência: {total:.0f} kWh/mês", x=0.02, ha="left", color=COR["texto"])
    estilo(ax)
    fig.tight_layout()
    fig.savefig(GRAF / "01_consumo_por_aparelho.png", dpi=150)
    plt.close(fig)

    # 2) conta mensal antes e depois (família A x B)
    alts = ["Hoje"] + [c["alternativa"].split(" · ")[1] for c in comp[:4]]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    largura = 0.38
    for k, (fam, cor) in enumerate((("Família A (com Tarifa Social)", COR["s1"]), ("Família B (sem Tarifa Social)", COR["s2"]))):
        linhas = [c for c in comp if c["familia"] == fam]
        vals = [linhas[0]["conta_base_rs_mes"]] + [c["conta_apos_rs_mes"] for c in linhas]
        xs = [x + (k - 0.5) * (largura + 0.02) for x in range(len(alts))]
        ax.bar(xs, vals, width=largura, color=cor, label=fam)
        for x, v in zip(xs, vals):
            ax.text(x, v + 3, f"R${v:.0f}", ha="center", fontsize=8.5, color=COR["texto2"])
    ax.set_xticks(range(len(alts)), alts, fontsize=9.5)
    ax.set_ylabel("R$ por mês (energia, sem bandeira)")
    ax.set_title("Conta de energia estimada no 1º ano, por alternativa", loc="left", color=COR["texto"])
    ax.legend(frameon=False, loc="upper right")
    estilo(ax)
    fig.tight_layout()
    fig.savefig(GRAF / "02_conta_mensal_por_alternativa.png", dpi=150)
    plt.close(fig)

    # 3) saldo acumulado em 10 anos (família A)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    cores = [COR["s1"], COR["s2"], COR["s3"], COR["s4"]]
    fam = "Família A (com Tarifa Social)"
    nomes_alt = list(dict.fromkeys(f["alternativa"] for f in fluxos if f["familia"] == fam))
    for nome, cor in zip(nomes_alt, cores):
        serie = [f for f in fluxos if f["familia"] == fam and f["alternativa"] == nome]
        anos = [f["ano"] for f in serie]
        acc = [f["acumulado_rs"] for f in serie]
        ax.plot(anos, acc, color=cor, linewidth=2, marker="o", markersize=4, label=nome)
        ax.text(10.15, acc[-1], nome.split(" · ")[1], va="center", fontsize=9, color=COR["texto2"])
    ax.axhline(0, color=COR["texto2"], linewidth=0.8)
    ax.set_xlim(0, 13.2)
    ax.set_xticks(range(0, 11))
    ax.set_xlabel("anos após o investimento")
    ax.set_ylabel("saldo acumulado (R$)")
    ax.set_title("Família A: quando cada alternativa se paga (valores reais, sem reajuste)", loc="left", color=COR["texto"])
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    estilo(ax)
    fig.tight_layout()
    fig.savefig(GRAF / "03_saldo_acumulado_familia_A.png", dpi=150)
    plt.close(fig)


def main():
    comp, fluxos, itens = tabelas()
    graficos(comp, fluxos, itens)
    print(f"Resultados gravados em {SAIDA}")
    for c in comp:
        print(f"{c['familia'][:9]} | {c['alternativa']:34} | invest R$ {c['investimento_rs']:>8.2f} | "
              f"economia/ano R$ {c['economia_ano1_rs']:>8.2f} | payback {c['payback_anos']} anos")


if __name__ == "__main__":
    main()
