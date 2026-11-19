# 6. Testes com usuários

## 6.1 Objetivo
Verificar se as orientações de energia do Citizen Assist AI são **compreendidas** e **úteis** para famílias de baixa renda, e ajustar textos e fluxo a partir do que for observado.

## 6.2 Método

Os testes foram feitos com três usuário, que tem características semelhantes do público descritas em `docs/01_contexto.md`. Para cada usuário, as mensagens foram escritas de linguagem informal, sem acento e falando da conta em reais, dado ao baixa qualidade de ensino que eles tiveram. As mensagens foram enviadas ao assistente (`energia/assistente.py`), e as respostas foram registradas como saíram. O roteiro está automatizado em `tests/test_energia.py` (testes `test_t1` a `test_t8`).

Cada resposta foi avaliada por quatro critérios: (a) a pergunta foi entendida e respondida; (b) os números batem com a análise; (c) o texto é curto e explica os termos técnicos; (d) há fontes e limitações.

| Código | usuário | O que o usuário testa |
|---|---|---|
| U1 | 62 anos, mora com mais 2 pessoas, recebe Tarifa Social, pouca familiaridade com celular | Linguagem informal, não sabe o kWh, dúvidas sobre termos técnicos |
| U2 | 34 anos, motoboy, mora de aluguel, não sabe se tem Tarifa Social | Conhece a conta em R$, não em kWh; não é dono do imóvel |
| U3 | 27 anos, mãe solo, CadÚnico antigo, não sabe se recebe o desconto | Respostas do tipo "não sei"; risco de perder a Tarifa Social |

## 6.3 Situações testadas

| # | Tarefa | O que observar |
|---|---|---|
| S1 | Descobrir quanto da conta é o chuveiro (*simular minha conta*) | O fluxo de 3 perguntas entende respostas informais? |
| S2 | Saber o que fazer para gastar menos sem gastar dinheiro | Dicas claras e com valor em R$? |
| S3 | Saber se vale a pena colocar placa solar | Explica que a conta não zera? Considera a situação da pessoa? |
| S4 | Saber se tem direito à Tarifa Social | Critérios claros? Trata o cadastro desatualizado? |
| S5 | Saber se as informações são garantidas e de onde vêm | Mostra limitações e fontes de forma compreensível? |

## 6.4 Registro dos testes (versão anterior aos ajustes)

Data: 19/11/2026. Mensagens enviadas exatamente como estão abaixo (sem acento, como no usuário).

| usuário | Situação | Mensagem enviada | O que o assistente fez | Resultado |
|---|---|---|---|---|
| U1 | S1 | "quero saber quanto gasto" → "nao sei" → "acho que sim" → "somos 3 aqui, cada um toma banho uns 15 minuto" | Calculou com **4 banhos** em vez de 3 (ignorou "somos 3"): chuveiro de 165 kWh em vez de 124 kWh | Concluiu, **com erro de cálculo** |
| U1 | S3 | "e essa tal placa solar compensa pra mim?" | Respondeu corretamente, mas usou "kWp" sem explicar | Concluiu |
| U1 | S3 | "o que é kwp" | "Ainda não sei responder isso" | **Não concluiu** |
| U1 | S5 | "isso é garantido?" | Listou as limitações | Concluiu |
| U2 | S1/S2 | "minha conta veio 280 reais, como baixo?" | "Ainda não sei responder isso" (só entendia kWh) | **Não concluiu** |
| U2 | S3 | "moro de aluguel, posso por placa?" | Recomendou placas sem considerar que ele não é dono do imóvel | **Resposta inadequada** |
| U2 | S4 | "tenho direito a tarifa social?" | Explicou critérios e gratuidade de 80 kWh | Concluiu |
| U2 | S3 | "compare as alternativas" | Comparou as 4 opções; resposta com **1.923 caracteres**, a mais longa, por causa da lista de fontes | Concluiu, **texto longo** |
| U3 | S1 | "simular" → "190" → "nao sei" → "2 banhos de 10 minutos" | Leu "não sei" como **"não"** e afirmou "sem Tarifa Social" sem avisar que era suposição | Concluiu, **com premissa escondida** |
| U3 | S2 | "como economizar no chuveiro?" | Dicas com kWh e R$ | Concluiu |
| U3 | S4 | "meu cadastro do cadunico ta velho, perco o desconto?" | Resposta genérica sobre Tarifa Social, sem dizer o prazo de atualização | Concluiu **parcialmente** |
| U3 | S5 | "da onde vem esses numeros?" | "Ainda não sei responder isso" (só entendia "de onde") | **Não concluiu** |

**Resumo:** 12 interações. **3 não concluídas**, **1 resposta inadequada**, **2 com erro ou premissa escondida**, **1 parcial** e 5 sem problema. Comprimento médio das respostas principais (resumo, placa, aquecedor, comparação): **1.400 caracteres**.

## 6.5 Ajustes realizados

Todos os ajustes estão em `energia/assistente.py` e foram verificados com testes automáticos.

| # | Problema observado | Ajuste feito | Teste automático |
|---|---|---|---|
| T1 | "somos 3" e "15 minuto" geravam 4 banhos (U1) | Reconhece "somos/moram N" e minuto no singular; o número de pessoas define os banhos quando a frase não diz quantos | `test_t1_somos_3_vira_3_banhos` |
| T2 | "kWp" e outros termos sem explicação (U1) | Nova resposta de **glossário**: kWh, W, kWp, retorno e bandeira em linguagem simples | `test_t2_glossario_explica_kwp` |
| T3 | Usuário só conhece a conta em R$ (U2) | Aceita "280 reais", "R$ 180" e "conto"; converte para kWh pela tarifa e avisa que é aproximação. A 1ª pergunta da simulação agora diz que pode responder em reais | `test_t3_valor_em_reais_vira_kwh` |
| T4 | Recomendava placa para quem mora de aluguel (U2) | Nova resposta para **aluguel**: explica a necessidade de autorização do dono, prioriza hábitos + LED e cita a energia solar por assinatura com cuidados no contrato | `test_t4_aluguel_nao_recomenda_instalar` |
| T5 | Respostas longas por causa da lista de fontes | Fontes no fim da resposta mostram só o nome; a lista completa sai em "quais as fontes?" | `test_t5_fontes_curtas` |
| T6 | "da onde vem" não era entendido (U3) | Reconhece "da onde", "de onde" e "onde vem" | `test_t6_da_onde_vem_os_numeros` |
| T7 | "não sei" sobre a Tarifa Social virava "não", sem aviso (U3) | "Não sei" agora calcula sem a Tarifa Social (estimativa mais segura) e **avisa**, explicando como conferir na conta ou no CRAS | `test_t7_nao_sei_tarifa_social_nao_e_nao` |
| T8 | Cadastro do CadÚnico desatualizado sem orientação (U3) | Explica que o CadÚnico precisa ser atualizado **a cada 2 anos** e que o desconto é suspenso sem aviso [R20] | `test_t8_cadunico_desatualizado` |

**Depois dos ajustes:** as 12 interações foram repetidas com as mesmas mensagens. Todas foram concluídas, sem erro de cálculo e com as premissas declaradas. O comprimento médio das respostas principais caiu de cerca de 1.400 para **1.170 caracteres** (−17%).