"""
Módulo de energia do Citizen Assist AI.

O assistente responde a perguntas em linguagem simples usando SOMENTE os
resultados calculados em energia/cenarios.py. Cada resposta traz:
  - a orientação (o que fazer),
  - os números que a sustentam (kWh, R$, prazo de retorno, CO2),
  - as fontes usadas,
  - as condições e limitações da estimativa.

Usamos regras (palavras-chave) em vez de um modelo generativo de propósito:
assim a resposta é sempre coerente com a análise e auditável pelo professor.
"""

import re
import unicodedata
from dataclasses import dataclass, field

from . import calculos as C
from . import cenarios as S
from . import parametros as P

AVISO = ("Isto é uma ESTIMATIVA, não um valor garantido. A conta real muda com "
         "bandeira tarifária, impostos do mês, clima e hábitos da casa.")


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------
def normalizar(texto):
    t = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def reais(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def num(v, casas=0):
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def prazo(anos):
    if anos == float("inf"):
        return "não se paga em 10 anos"
    if anos < 1:
        meses = max(1, round(anos * 12))
        return f"cerca de {meses} {'mês' if meses == 1 else 'meses'}"
    return f"cerca de {num(anos, 1)} anos"


def fontes(*ids):
    return "📚 Fontes: " + "; ".join(f"[{i}] {P.FONTES[i]}" for i in ids)


def limites(*itens):
    return "⚠️ Limitações: " + " ".join(itens) + " " + AVISO


# ---------------------------------------------------------------------------
# Sessão (guarda o perfil do usuário durante a conversa)
# ---------------------------------------------------------------------------
@dataclass
class Sessao:
    perfil: S.Perfil = field(default_factory=lambda: S.perfil_referencia(True))
    personalizado: bool = False
    tarifa_social_informada: bool = False
    aguardando: str | None = None      # próxima pergunta da simulação


class AssistenteEnergia:
    def __init__(self):
        self.sessao = Sessao()

    # ------------------------------------------------------------------
    def responder(self, mensagem: str) -> str:
        t = normalizar(mensagem).strip()
        if not t:
            return "Pode perguntar! Digite **ajuda** para ver o que eu sei fazer."

        # 1) extrai dados que o usuário contou (kWh, banhos, minutos, tarifa social)
        captou = self._extrair_dados(t)

        # 2) se estamos no meio da simulação, continua o roteiro
        if self.sessao.aguardando:
            return self._continuar_simulacao(t, captou)

        # usuário contou o consumo sem fazer pergunta → devolve a estimativa personalizada
        if captou and re.search(r"\d\s*(kwh|kw/h)", t) and "?" not in mensagem:
            return self._resumo_personalizado(prefixo="Anotei seus dados. ")

        intencoes = [
            (r"\b(ajuda|menu|o que voce faz|oi|ola|bom dia|boa tarde|boa noite)\b", self.ajuda),
            (r"\b(fontes?|referencias?|de onde (vem|vieram|tirou))\b", self.referencias),
            (r"\b(limitac|premissa|garantid|certeza|precis)", self.limitacoes),
            (r"\b(simul|estimar|calcular (a )?minha|quanto (eu )?gasto|meu consumo)", self.iniciar_simulacao),
            (r"\b(compar|alternativas|qual (e )?(a )?melhor|qual escolher|melhor opcao)", self.comparar),
            (r"\b(fio b|14\.?300|taxa do sol|creditos?|compensacao)\b", self.fio_b),
            (r"\b(golpe|orcamento|empresa|instalador|contratar|financ)", self.cuidados_compra),
            (r"\b(placas?|paineis|painel|fotovolta|energia solar|gerar (minha )?(propria )?energia)", self.fotovoltaica),
            (r"\b(aquecedor|aquecimento solar|boiler|agua quente)", self.aquecedor),
            (r"\b(tarifa social|cadunico|cad unico|baixa renda|bpc|isencao)", self.tarifa_social),
            (r"\b(chuveiro|banho)", self.chuveiro),
            (r"\b(lampadas?|led|iluminacao|luz acesa)\b", self.iluminacao),
            (r"\b(geladeira|refrigerador|freezer)", self.geladeira),
            (r"\b(co2|carbono|emiss|meio ambiente|ambiental|sustentav|planeta)", self.ambiental),
            (r"\b(dicas?|economizar|economia|reduzir|baixar a conta|conta alta|gastar menos)", self.dicas),
            (r"\b(vale a pena|compensa|investir)", self.comparar),
        ]
        for padrao, func in intencoes:
            if re.search(padrao, t):
                return func()
        if captou:
            return self._resumo_personalizado(prefixo="Anotei seus dados. ")
        return ("Ainda não sei responder isso. Posso ajudar com: conta de luz, chuveiro, "
                "lâmpadas, geladeira, Tarifa Social, aquecedor solar, placas solares e "
                "comparação entre elas. Digite **ajuda** para ver exemplos.")

    # ------------------------------------------------------------------
    # Extração de dados e simulação
    # ------------------------------------------------------------------
    def _extrair_dados(self, t):
        p, captou = self.sessao.perfil, False
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(kwh|kw/h|quilowatt)", t)
        if m:
            p.consumo_informado_kwh = float(m.group(1).replace(",", "."))
            captou = True
        m = re.search(r"(\d+)\s*(banhos|banho)", t)
        if m:
            p.banhos_dia = int(m.group(1)); captou = True
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(min|minutos)", t)
        if m:
            p.minutos_banho = float(m.group(1).replace(",", ".")); captou = True
        m = re.search(r"(\d+)\s*(pessoas|moradores)", t)
        if m:
            p.pessoas = int(m.group(1)); p.banhos_dia = p.pessoas; captou = True
        if re.search(r"(nao|sem) (tenho |recebo |tem )?(a )?tarifa social", t):
            p.tarifa_social = False; self.sessao.tarifa_social_informada = True; captou = True
        elif re.search(r"(tenho|recebo|com|uso) (a )?tarifa social", t):
            p.tarifa_social = True; self.sessao.tarifa_social_informada = True; captou = True
        if captou:
            self.sessao.personalizado = True
        return captou

    def iniciar_simulacao(self):
        self.sessao.aguardando = "kwh"
        return ("Vamos estimar a sua conta e onde dá para economizar. 🧮\n"
                "1/3 · Quantos **kWh** a sua casa consumiu no último mês? Esse número fica na "
                "conta de luz, no campo *Consumo* ou no gráfico de histórico. "
                "Se não souber, responda **não sei** que eu uso uma família de referência (≈198 kWh).")

    def _continuar_simulacao(self, t, captou):
        etapa, p = self.sessao.aguardando, self.sessao.perfil
        if re.search(r"\b(cancelar|sair|parar)\b", t):
            self.sessao.aguardando = None
            return "Simulação cancelada. Pode me perguntar outra coisa."
        if etapa == "kwh":
            n = re.search(r"\d+(?:[.,]\d+)?", t)
            if n and not captou:
                p.consumo_informado_kwh = float(n.group(0).replace(",", "."))
            elif "nao sei" in t:
                p.consumo_informado_kwh = None
            self.sessao.aguardando = "ts"
            return ("2/3 · Sua família recebe a **Tarifa Social** (desconto da conta para quem está "
                    "no CadÚnico ou recebe BPC)? Responda **sim**, **não** ou **não sei**.")
        if etapa == "ts":
            if re.search(r"\bsim\b", t):
                p.tarifa_social = True
            elif re.search(r"\bnao\b", t):
                p.tarifa_social = False
            self.sessao.tarifa_social_informada = True
            self.sessao.aguardando = "banho"
            return ("3/3 · Quantos banhos de **chuveiro elétrico** por dia na casa e quantos minutos "
                    "dura cada um, mais ou menos? Ex.: *4 banhos de 10 minutos*.")
        if etapa == "banho":
            nums = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", t)]
            if not captou and len(nums) >= 2:
                p.banhos_dia, p.minutos_banho = int(nums[0]), nums[1]
            self.sessao.aguardando = None
            self.sessao.personalizado = True
            return self._resumo_personalizado()
        self.sessao.aguardando = None
        return self.ajuda()

    def _resumo_personalizado(self, prefixo=""):
        p = self.sessao.perfil
        conta = C.conta_mensal(p.consumo_kwh, p.tarifa_social)
        a1 = S.alternativa_eficiencia(p)
        a2 = S.alternativa_aquecedor_solar(p)
        a3 = S.alternativa_fotovoltaica(p)
        marg = C.valor_kwh_economizado(p.consumo_kwh, p.tarifa_social)
        partes = [prefixo + f"**Sua estimativa** ({num(p.consumo_kwh)} kWh/mês, "
                  f"{'com' if p.tarifa_social else 'sem'} Tarifa Social):",
                  f"• Energia na conta: **{reais(conta)} por mês** (sem bandeira e sem iluminação pública).",
                  f"• Seu chuveiro gasta cerca de **{num(p.chuveiro_kwh)} kWh/mês** "
                  f"({num(100 * p.chuveiro_kwh / max(p.consumo_kwh, 1))}% do consumo)."]
        if p.consumo_informado_kwh is not None and p.chuveiro_kwh > 0.8 * p.consumo_informado_kwh:
            partes.append(f"• ⚠️ Com {p.banhos_dia} banhos de {num(p.minutos_banho)} min por dia, o chuveiro gastaria quase "
                          "tudo (ou mais) do que a conta mostra. Me conte quantos banhos e minutos são de verdade, "
                          "ou confira a potência na etiqueta do chuveiro.")
        if p.tarifa_social and p.consumo_kwh <= P.TSEE_FAIXA_GRATUITA.valor:
            partes.append("• Você está dentro dos 80 kWh gratuitos: economizar mais não reduz a conta "
                          "agora, mas evita que ela volte a ser cobrada. Placa solar **não compensa** no seu caso.")
        else:
            partes.append(f"• Cada kWh que você deixa de gastar vale **{reais(marg)}**.")
            partes.append(f"\n**1º passo — hábitos e LED:** economia de ~{num(a1.kwh_economizados_mes)} kWh/mês "
                          f"(≈ {reais(a1.economia_ano1 / 12)}/mês) gastando ~{reais(a1.investimento)}. "
                          f"Retorno em {prazo(a1.payback_anos)}.")
            partes.append(f"**Aquecedor solar:** ≈ {reais(a2.economia_ano1 / 12)}/mês, investimento "
                          f"~{reais(a2.investimento)}, retorno em {prazo(a2.payback_anos)}.")
            partes.append(f"**Placas solares ({num(a3.detalhes['kwp'], 2)} kWp):** ≈ {reais(a3.economia_ano1 / 12)}/mês "
                          f"no 1º ano, investimento ~{reais(a3.investimento)}, retorno em {prazo(a3.payback_anos)}.")
        if not self.sessao.tarifa_social_informada:
            partes.append("\nℹ️ Considerei que você tem Tarifa Social. Se não tiver, me diga "
                          "\"não tenho tarifa social\" que eu refaço a conta.")
        partes.append("\n" + limites("Tarifa Enel SP (B1) após o reajuste de jul/2026.",
                                     "Consumo do chuveiro calculado com 5.500 W."))
        partes.append(fontes("R1", "R2", "R3", "R17"))
        return "\n".join(partes)

    # ------------------------------------------------------------------
    # Respostas temáticas
    # ------------------------------------------------------------------
    def ajuda(self):
        return ("Olá! Sou o módulo de **energia** do Citizen Assist AI. ⚡ Ajudo famílias a "
                "entender e reduzir a conta de luz. Experimente perguntar:\n"
                "• *simular minha conta*\n• *como economizar no chuveiro?*\n"
                "• *vale a pena colocar placa solar?*\n• *aquecedor solar compensa?*\n"
                "• *compare as alternativas*\n• *tenho direito à tarifa social?*\n"
                "• *qual o impacto no meio ambiente?*\n• *quais as fontes?* / *quais as limitações?*\n"
                "Você também pode contar seus dados, ex.: *gasto 250 kWh, somos 5 pessoas, banho de 12 minutos*.")

    def dicas(self):
        p = self.sessao.perfil
        itens, _ = S.economia_habitos_kwh(p)
        a1 = S.alternativa_eficiencia(p)
        linhas = [f"Comece pelo que é quase de graça. Para {'a sua casa' if self.sessao.personalizado else 'uma família de 4 pessoas'}:"]
        for nome, kwh in sorted(itens.items(), key=lambda x: -x[1]):
            linhas.append(f"• {nome}: −{num(kwh, 1)} kWh/mês")
        linhas.append(f"\nTotal: ~{num(a1.kwh_economizados_mes)} kWh/mês ≈ **{reais(a1.economia_ano1 / 12)} por mês**, "
                      f"gastando ~{reais(a1.investimento)} em lâmpadas LED (retorno em {prazo(a1.payback_anos)}).")
        linhas.append(limites("Supõe que todos na casa adotem os hábitos; com metade da adesão a economia cai pela metade."))
        linhas.append(fontes("R1", "R17", "R18"))
        return "\n".join(linhas)

    def chuveiro(self):
        p = self.sessao.perfil
        itens, depois = S.economia_habitos_kwh(p)
        reducao = list(itens.values())[0]
        por_min = p.potencia_chuveiro_w / 1000 / 60 * P.TARIFA_COM_TRIBUTOS.valor
        return (f"O chuveiro elétrico é o maior gasto da casa: ~{num(p.chuveiro_kwh)} kWh/mês "
                f"({p.banhos_dia} banhos de {num(p.minutos_banho)} min a {num(p.potencia_chuveiro_w)} W). "
                f"Cada minuto de banho na posição inverno custa ~{reais(por_min)}.\n"
                f"• Reduzir cada banho em 2 minutos e usar a posição **verão** nos meses quentes economiza "
                f"~{num(reducao, 1)} kWh/mês (≈ {reais(reducao * P.TARIFA_COM_TRIBUTOS.valor)}/mês).\n"
                "• Fechar o registro ao se ensaboar e evitar banhos no horário de pico (18h–21h) também ajuda a rede.\n"
                "• Para quem toma banhos longos ou tem família grande, o **aquecedor solar** pode valer a pena "
                "(pergunte \"aquecedor solar compensa?\").\n"
                + limites("Potência verão considerada de 3.200 W; confira a do seu aparelho na etiqueta.")
                + "\n" + fontes("R1", "R17", "R18"))

    def iluminacao(self):
        p = self.sessao.perfil
        itens, _ = S.economia_habitos_kwh(p)
        led = [v for k, v in itens.items() if "LED" in k][0]
        qtd = p.lampadas_incandescentes + p.lampadas_fluorescentes
        return (f"Trocar {qtd} lâmpadas antigas por **LED de 9 W** economiza ~{num(led, 1)} kWh/mês "
                f"(≈ {reais(led * P.TARIFA_COM_TRIBUTOS.valor)}/mês) e custa ~{reais(qtd * S.CUSTO_LED_UN)}. "
                "Uma LED de 9 W ilumina como uma incandescente de 60 W gastando ~85% menos.\n"
                "• Prefira lâmpadas com selo Procel/Inmetro.\n• Fluorescentes têm mercúrio: leve a pontos de coleta.\n"
                + limites("Uso estimado de 3 h/dia (incandescentes) e 5 h/dia (fluorescentes); preço de R$ 12 por LED.")
                + "\n" + fontes("R17"))

    def geladeira(self):
        p = self.sessao.perfil
        eco = p.geladeira_kwh_mes * S.REDUCAO_GELADEIRA
        return (f"A geladeira fica ligada 24 h e gasta ~{num(p.geladeira_kwh_mes)} kWh/mês numa casa típica. "
                f"Cuidados simples podem cortar ~10% (≈ {num(eco, 1)} kWh ou {reais(eco * P.TARIFA_COM_TRIBUTOS.valor)}/mês):\n"
                "• Teste a borracha: feche a porta numa folha de papel; se ela sair fácil, troque a vedação.\n"
                "• Deixe 15 cm entre a parede e a grade de trás e longe do fogão.\n"
                "• Não guarde comida quente e não abra a porta à toa.\n"
                "• Se for trocar, procure a etiqueta **A** do Inmetro/Procel e descarte a velha em ponto de coleta "
                "(o gás de refrigeração não pode ir para o ar).\n"
                + limites("Redução de 10% é uma estimativa média; geladeiras muito antigas podem gastar bem mais.")
                + "\n" + fontes("R17"))

    def tarifa_social(self):
        return ("A **Tarifa Social de Energia Elétrica** dá **gratuidade nos primeiros 80 kWh do mês** para:\n"
                "• famílias no CadÚnico com renda de até meio salário mínimo por pessoa;\n"
                "• pessoas que recebem o BPC (idosos e pessoas com deficiência);\n"
                "• também há regras para indígenas, quilombolas e quem usa aparelhos médicos elétricos.\n"
                "O que passar de 80 kWh é cobrado pela tarifa normal. O benefício é automático, mas a conta precisa "
                "estar no nome de alguém da família e o CadÚnico precisa estar **atualizado** — cadastro antigo faz "
                "perder o desconto. Dúvidas: CRAS da sua cidade ou a Enel.\n"
                "💡 Por isso, para quem tem a Tarifa Social, cada kWh economizado ACIMA de 80 kWh vale a tarifa cheia "
                f"(~{reais(P.TARIFA_COM_TRIBUTOS.valor)}).\n"
                + limites("Regras podem mudar; confirme na distribuidora. Iluminação pública e outros itens continuam na conta.")
                + "\n" + fontes("R3"))

    def aquecedor(self):
        p = self.sessao.perfil
        a2 = S.alternativa_aquecedor_solar(p)
        a2b = S.alternativa_aquecedor_solar(p, custo=P.CUSTO_AQUECEDOR_SOLAR_MIN.valor)
        veredito = ("vale a pena no longo prazo" if a2.payback_anos <= 6 else
                    "se paga devagar com o seu uso atual; compensa mais em famílias grandes ou com banhos longos")
        return (f"O **aquecedor solar de água** usa o calor do sol (energia renovável) para esquentar a água do banho. "
                f"Com ~{num(P.FRACAO_SOLAR.valor * 100)}% do aquecimento vindo do sol, ele evitaria "
                f"~{num(a2.kwh_economizados_mes)} kWh/mês do chuveiro (≈ {reais(a2.economia_ano1 / 12)}/mês).\n"
                f"• Investimento: ~{reais(a2.investimento)} (há casos de {reais(a2b.investimento)}), "
                f"mais ~{reais(P.MANUTENCAO_AQUECEDOR.valor)}/ano de manutenção.\n"
                f"• Retorno: {prazo(a2.payback_anos)} (ou {prazo(a2b.payback_anos)} no preço menor) → {veredito}.\n"
                "• Precisa de telhado com sol, caixa d'água e espaço para um reservatório de ~200 L.\n"
                "• Bônus: tira o chuveiro do horário de pico, quando a rede é mais cara e mais poluente.\n"
                + limites("Fração solar de 65% é média anual estimada; em dias nublados o chuveiro elétrico complementa.")
                + "\n" + fontes("R12", "R13", "R1"))

    def fotovoltaica(self):
        p = self.sessao.perfil
        a3 = S.alternativa_fotovoltaica(p)
        d = a3.detalhes
        if p.tarifa_social and p.consumo_kwh <= P.TSEE_FAIXA_GRATUITA.valor + 20:
            return ("Com a Tarifa Social e consumo perto de 80 kWh, quase toda a sua energia já é gratuita: "
                    "placas solares **não compensam** no seu caso. Foque em manter o consumo baixo.\n"
                    + limites("Considera as regras da Tarifa Social de 2026.") + "\n" + fontes("R3", "R4"))
        ano1 = d["contas_por_ano"][0]
        return (f"**Placas solares (fotovoltaica)** geram eletricidade com a luz do sol. Para "
                f"{num(p.consumo_kwh)} kWh/mês, um sistema de **{num(d['kwp'], 2)} kWp** ({d['modulos']} placas, "
                f"~{num(d['area_m2'])} m² de telhado) geraria ~{num(d['geracao_kwh_mes'])} kWh/mês.\n"
                f"• Investimento: ~{reais(a3.investimento)} (faixa de mercado "
                f"{reais(d['kwp'] * 1000 * P.PRECO_FV_POR_WP_MIN.valor)} a {reais(d['kwp'] * 1000 * P.PRECO_FV_POR_WP_MAX.valor)}).\n"
                f"• Conta de energia cai de {reais(d['conta_sem_fv'])} para ~{reais(ano1[2])} por mês em {ano1[0]} — "
                f"ela não zera por causa do **Fio B** e do valor mínimo da conta.\n"
                f"• Retorno: {prazo(a3.payback_anos)}; em 10 anos sobra ~{reais(a3.economia_acumulada)} já descontado o investimento.\n"
                "• Precisa de telhado próprio, firme, com sol e de projeto homologado na Enel.\n"
                + limites("A parcela do Fio B cobrada sobe para 75% em 2027 e 90% em 2028; após 2028 a regra não está definida.",
                          "Geração estimada com irradiação de 4,63 kWh/m².dia e 75% de rendimento.",
                          *(["Com Tarifa Social, confirme com a Enel como os créditos se combinam com os 80 kWh gratuitos."]
                            if p.tarifa_social else []))
                + "\n" + fontes("R4", "R5", "R7", "R9", "R10"))

    def fio_b(self):
        return ("Quem gera energia em casa (Lei 14.300/2022) manda o excedente para a rede e ganha **créditos**. "
                "Mas parte da tarifa — o **Fio B**, que paga o uso dos fios da distribuidora — não é devolvida. "
                "A parte não compensada sobe todo ano: 60% em 2026, 75% em 2027 e 90% em 2028. "
                f"Na nossa conta isso custa ~{reais(P.FIO_B_SEM_TRIBUTOS.valor * P.FATOR_TRIBUTOS.valor * 0.75)} "
                "por kWh compensado em 2027. Os créditos valem por 60 meses.\n"
                "💡 Por isso placa solar NÃO zera a conta, e usar a energia na hora (de dia) rende mais que injetar.\n"
                + limites("Valor do Fio B da Enel SP estimado (0,22 R$/kWh sem impostos).")
                + "\n" + fontes("R4", "R5"))

    def comparar(self):
        p = self.sessao.perfil
        res = S.comparar(p)
        linhas = [f"Comparação para {num(p.consumo_kwh)} kWh/mês ({'com' if p.tarifa_social else 'sem'} Tarifa Social), "
                  "mesma casa, mesmos 12 meses e 10 anos de horizonte:\n"]
        for r in res:
            linhas.append(f"**{r.nome}** {'🌱' if r.renovavel else ''}\n"
                          f"   investe {reais(r.investimento)} · economiza ~{reais(r.economia_ano1 / 12)}/mês · "
                          f"retorno {prazo(r.payback_anos)} · saldo em 10 anos {reais(r.economia_acumulada)} · "
                          f"evita {num(r.co2_evitado_kg_ano)} kg CO₂/ano")
        linhas.append("\n**Recomendação:** 1º) hábitos + LED sempre — retorno quase imediato. "
                      "2º) Se a família tem telhado próprio e consegue investir, as placas solares têm o melhor saldo "
                      "em 10 anos; o aquecedor solar é a opção renovável mais simples quando os banhos pesam muito na conta. "
                      "Antes de investir, peça 3 orçamentos (pergunte \"cuidados ao contratar\").")
        linhas.append(limites("Valores reais constantes (sem inflação da tarifa).",
                              "Emissões pequenas porque a eletricidade brasileira já é majoritariamente renovável."))
        linhas.append(fontes("R1", "R2", "R4", "R9", "R12", "R14"))
        return "\n".join(linhas)

    def ambiental(self):
        p = self.sessao.perfil
        res = {r.nome: r for r in S.comparar(p)}
        a1, a2, a3 = (res[k] for k in list(res)[:3])
        return ("A eletricidade do Brasil é bem renovável (hidrelétricas, eólica, solar), então cada kWh emite pouco: "
                f"~{num(P.FATOR_EMISSAO_SIN.valor * 1000)} g de CO₂ em média. Por ano, para esta casa:\n"
                f"• Hábitos + LED: −{num(a1.co2_evitado_kg_ano)} kg CO₂ (e menos lixo eletrônico com lâmpadas que duram mais).\n"
                f"• Aquecedor solar: −{num(a2.co2_evitado_kg_ano)} kg CO₂ e menos consumo no horário de pico, quando "
                "usinas térmicas a gás e carvão são acionadas.\n"
                f"• Placas solares: −{num(a3.co2_evitado_kg_ano)} kg CO₂ já descontando a fabricação das placas. "
                "No fim da vida útil (25+ anos) os módulos precisam ser reciclados.\n"
                "💡 O maior ganho ambiental é **não desperdiçar**: energia que não é usada não precisa ser gerada nem transmitida.\n"
                + limites("Fator médio anual; em meses secos com mais térmicas o benefício é maior.")
                + "\n" + fontes("R14", "R15", "R16"))

    def cuidados_compra(self):
        return ("Antes de contratar placas ou aquecedor solar:\n"
                "• Peça pelo menos **3 orçamentos** de empresas com CNPJ, endereço e avaliações.\n"
                "• Exija que a simulação de economia inclua o **Fio B** e o valor mínimo da conta.\n"
                "• Desconfie de promessa de \"conta zero\" ou de quem pede pagamento total antes do projeto.\n"
                "• Confirme que o projeto será **homologado na Enel** e que há garantia de instalação.\n"
                "• Financiamento: compare a parcela com a economia; ela deve caber com folga.\n"
                + limites("Orientação geral, não é aconselhamento financeiro.") + "\n" + fontes("R4", "R5"))

    def referencias(self):
        return "Todas as contas usam estas fontes (detalhes em docs/05_referencias.md):\n" + \
               "\n".join(f"[{k}] {v}" for k, v in P.FONTES.items())

    def limitacoes(self):
        return ("O que você precisa saber sobre as minhas estimativas:\n"
                f"• Tarifa usada: {reais(P.TARIFA_COM_TRIBUTOS.valor)}/kWh (Enel SP B1, jul/2026, com impostos, bandeira verde).\n"
                "• Bandeiras amarela/vermelha aumentam a conta e a economia em reais.\n"
                "• Consumo dos aparelhos é estimado; o real depende do modelo e do uso.\n"
                "• Geração solar varia com clima, sombra e inclinação do telhado.\n"
                "• Preços de equipamentos variam por região e empresa.\n"
                "• Regras do Fio B após 2028 ainda não foram definidas.\n"
                "• Não substituo orçamento técnico nem orientação da distribuidora.\n" + AVISO)
