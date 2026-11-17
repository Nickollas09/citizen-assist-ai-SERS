# 4. Recomendações, justificativas e limitações

## 4.1 Recomendações (como o assistente orienta)

| Situação da família | Recomendação | Justificativa (custo · viabilidade · ambiente) |
|---|---|---|
| **Qualquer família** | Hábitos + LED primeiro: banho 2 min mais curto, posição verão, LED, vedação da geladeira, desligar standby | R$ 72 de investimento, retorno ~1 mês, ~57 kWh/mês a menos; sem obra; menor impacto ambiental |
| Tem Tarifa Social e consome **até ~100 kWh** | **Não** investir em placas; manter o consumo baixo e o CadÚnico atualizado | Os 80 kWh já são gratuitos; a geração teria pouco a compensar |
| Consumo bem acima de 80 kWh, **telhado próprio** e dinheiro disponível sem dívida cara | Fotovoltaica pequena (1–2 kWp), após A1 | Melhor saldo em 10 anos entre as renováveis (retorno ~3 anos), mas exige homologação; conta não zera |
| Família grande / banhos longos / chuveiro > 35% da conta | Aquecedor solar (após A1) | Retorno cai para ~4 anos em uso intenso; tira consumo do horário de pico |
| Mora de aluguel ou sem telhado adequado | Só A1 e, se possível, conversar com o proprietário | Instalações fixas exigem autorização e estrutura |
| Vai contratar instalação | 3 orçamentos, simulação com Fio B, homologação Enel, garantia; desconfiar de "conta zero" | Protege contra golpes e endividamento |

## 4.2 Condições e limitações das estimativas

As economias, gerações e custos são **estimativas**, nunca resultados garantidos. O assistente repete isso em toda resposta.

**Tarifa e conta**
- Tarifa de R$ 1,0135/kWh calculada para a Enel SP após 04/07/2026, com bandeira **verde**. Bandeiras amarela/vermelha aumentam a conta (e a economia em R$).
- PIS/COFINS variam todo mês; regras específicas de ICMS para baixo consumo não foram modeladas.
- Contribuição de iluminação pública não foi incluída (não muda entre alternativas).
- Próximo reajuste da Enel SP (jul/2027) não conhecido; cenário base sem aumento real da tarifa.

**Consumo**
- Inventário da família de referência é **estimado** a partir de médias Procel/Eletrobras/Idec. A conta real depende de modelos e hábitos; por isso o assistente pede o kWh da conta do usuário.
- Economia de hábitos supõe adesão de todos os moradores; com 50% de adesão a economia cai pela metade.

**Fotovoltaica**
- Irradiação de Mogi das Cruzes (RMSP) usada como aproximação; sombra, orientação e inclinação do telhado podem reduzir bastante a geração. Para um caso real, usar o CRESESB SunData com a localização exata.
- Valor do **Fio B** da Enel SP estimado (0,22 R$/kWh sem tributos); a regra após 2028 ainda não foi definida pela ANEEL (mantivemos 90%).
- Simultaneidade de 30% é premissa; famílias em casa de dia aproveitam mais.
- Modelo mensal pela média anual: não simula sazonalidade nem o banco de créditos (validade de 60 meses).
- A combinação **Tarifa Social × geração distribuída** foi modelada de forma simplificada (gratuidade aplicada ao consumo líquido) e deve ser confirmada com a distribuidora.
- Troca de inversor (~10–15 anos) fica fora do horizonte de 10 anos.

**Aquecedor solar**
- Fração solar de 65% é média anual estimada; varia com o projeto, o clima e o horário dos banhos.
- Custos de instalação variam muito com o telhado, a caixa d'água e a distância até o chuveiro.

**Ambiental**
- Fator de emissão médio anual do setor elétrico; o benefício marginal real no horário de pico tende a ser maior.

**Uso do assistente**
- Não substitui orçamento técnico, projeto elétrico, nem orientação da Enel ou do CRAS.
- Não é aconselhamento financeiro.
