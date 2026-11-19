# Ficha de teste com usuário (imprimir uma por participante)

**Código do participante:** P___  **Data:** ___/___/2026  **Avaliador (integrante):** ______________________

**Faixa etária:** ( ) 18–29 ( ) 30–44 ( ) 45–59 ( ) 60+  **Recebe Tarifa Social?** ( ) Sim ( ) Não ( ) Não sabe

> Antes de começar, leia para a pessoa: "Estamos testando um assistente que dá dicas sobre conta de luz. Quem está sendo testado é o assistente, não você. Não vamos anotar seu nome nem dados da sua conta. Você aceita participar?"  Aceitou? ( ) Sim

Não ajude a pessoa durante as tarefas. Anote o que ela fala em voz alta e onde ela trava.

| Tarefa (ler para a pessoa) | Concluiu? | Onde travou / o que disse |
|---|---|---|
| **S1** "Descubra quanto da sua conta é gasto com o chuveiro." | ( ) Sim ( ) Com dificuldade ( ) Não | |
| **S2** "Pergunte o que fazer para gastar menos sem gastar dinheiro." | ( ) Sim ( ) Com dificuldade ( ) Não | |
| **S3** "Pergunte se vale a pena colocar placa solar." | ( ) Sim ( ) Com dificuldade ( ) Não | |
| **S4** "Pergunte se você tem direito à Tarifa Social." | ( ) Sim ( ) Com dificuldade ( ) Não | |
| **S5** "Descubra se essas informações são garantidas." | ( ) Sim ( ) Com dificuldade ( ) Não | |

Perguntas de entendimento (resposta certa entre parênteses):
- "Depois de colocar placa solar, a conta fica zerada?" (Não) Acertou? ( ) Sim ( ) Não
- "O que dá para fazer primeiro, gastando quase nada?" (hábitos/LED) Acertou? ( ) Sim ( ) Não

**Questionário** (1 = discordo totalmente, 5 = concordo totalmente)

| Afirmação | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Q1. Entendi as respostas sem ajuda. | | | | | |
| Q2. As respostas foram úteis para a minha casa. | | | | | |
| Q3. Os números (kWh, R$, anos) foram fáceis de entender. | | | | | |
| Q4. Eu confiaria nessas orientações para tomar uma decisão. | | | | | |

**Q5. O que você mudaria?** ____________________________________________________________

______________________________________________________________________________________

## Depois dos testes

1. Passe cada ficha para a tabela da seção 6.4 de `docs/06_testes_com_usuarios.md` e calcule as médias de Q1 a Q4.
2. Para cada problema que se repetiu ou que impediu alguém de concluir uma tarefa, anote o ajuste na seção 6.5. Se for uma mudança de texto no assistente, ela fica em `energia/assistente.py`.
3. Rode `python -m pytest -q` depois de qualquer mudança no código.
4. Guarde as fichas em papel ou fotos **sem rosto e sem dados pessoais** como evidência, se o professor pedir.
