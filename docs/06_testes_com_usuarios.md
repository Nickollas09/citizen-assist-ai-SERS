# 6. Testes com usuários

> **Atenção, equipe:** as seções 6.4 e 6.5 devem ser preenchidas com os testes **reais** feitos com pessoas do público. Não inventar resultados.

## 6.1 Objetivo
Verificar se as orientações de energia do Citizen Assist AI são **compreendidas** e **úteis** para famílias de baixa renda, e ajustar textos e fluxo a partir dos comentários.

## 6.2 Protocolo
- **Participantes:** 3 a 5 pessoas do público (ou que convivem com ele), maiores de 18 anos.
- **Consentimento:** explicar o objetivo e pedir autorização verbal. Avisar que nenhum dado pessoal será registrado.
- **Privacidade:** registrar apenas um código (P1, P2…), faixa etária e se recebe Tarifa Social (sim/não/não sabe). **Não** registrar nome, endereço, CPF, nº de cliente nem foto da conta. A interface web não grava as mensagens.
- **Duração:** ~10 minutos por pessoa, no celular ou computador com `python -m app.web`.
- **Método:** a pessoa usa sozinha; o avaliador só observa e anota dúvidas (pensar em voz alta).

## 6.3 Situações testadas

| # | Tarefa dada ao participante | O que observar |
|---|---|---|
| S1 | "Descubra quanto da sua conta é o chuveiro." (usar *Simular minha conta*) | Achou o kWh na conta? Entendeu as 3 perguntas? |
| S2 | "Pergunte o que fazer para gastar menos sem gastar dinheiro." | Entendeu as dicas? Faria alguma? |
| S3 | "Pergunte se vale a pena colocar placa solar." | Entendeu que a conta não zera? Entendeu o prazo de retorno? |
| S4 | "Pergunte se tem direito à Tarifa Social." | Entendeu os critérios e o cuidado com o CadÚnico? |
| S5 | "Descubra se as informações são garantidas." | Notou as limitações e fontes? Confia mais ou menos por isso? |

**Questionário pós-uso** (escala 1 = discordo totalmente a 5 = concordo totalmente):
1. Entendi as respostas sem ajuda.
2. As respostas foram úteis para a minha casa.
3. Os números (kWh, R$, anos) foram fáceis de entender.
4. Eu confiaria nessas orientações para tomar uma decisão.
5. O que você mudaria? (aberta)

## 6.4 Registro dos testes (preencher)

| Participante | Perfil (faixa etária · TS) | Situação | Concluiu? | Dúvidas / comentários | Notas Q1–Q4 |
|---|---|---|---|---|---|
| P1 | [ ] | S1 | [ ] | [ ] | [ ] |
| P1 | | S2 | | | |
| P1 | | S3 | | | |
| P2 | [ ] | S1 | [ ] | [ ] | [ ] |
| … | | | | | |

**Resumo:** média Q1 [ ] · Q2 [ ] · Q3 [ ] · Q4 [ ] · principais comentários: [ ]

## 6.5 Ajustes realizados (preencher)

| Comentário / problema observado | Ajuste feito | Arquivo / commit |
|---|---|---|
| [ex.: participante não achou o kWh na conta] | [ex.: incluímos onde fica o campo "Consumo"] | [`energia/assistente.py`] |
| | | |

## 6.6 Pontos de atenção já tratados no projeto (antes dos testes)
Melhorias feitas pela equipe durante o desenvolvimento, para observar se funcionam com os usuários:
- A primeira pergunta da simulação explica **onde** encontrar o kWh na conta e aceita "não sei".
- Respostas usam R$/mês (mais familiar) além de kWh.
- Botões de atalho com as perguntas mais comuns (útil para quem tem dificuldade de digitar).
- Aviso quando os dados informados não fecham (ex.: chuveiro gastaria mais que a conta inteira).
- Contraste alto, fonte de 17 px e modo escuro automático na interface web.
