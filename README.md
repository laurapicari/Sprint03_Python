# ChargeVolt — Sprint 3: Prototipagem Funcional e Integração

**GoodWe ChargeGrid Intelligence Challenge**

Sistema de gerenciamento inteligente de recarga de veículos elétricos (VE), com integração de **energia renovável (solar + armazenamento)** e **automação da fonte de energia** utilizada em cada sessão de recarga.

> 🎥 **Vídeo técnico (até 5 min, YouTube não listado):** _COLE AQUI O LINK DO VÍDEO_

## 1. Equipe

- Beatriz Silva Araujo — RM 570619
- Gabriela Caetano Campos — RM 572738
- João Victor Montalvão — RM 571630
- Laura Pícari dos Santos Costa — RM 569914
- Lucas Neves Malaquias — RM 572679

---

### 2. Como cada componente se conecta

| Componente | Papel no sistema | Onde está no código |
|---|---|---|
| Assistente de IA | Estima demanda e ocupação por faixa de horário, informa a geração solar disponível e recomenda o melhor momento para recarregar. | `assistente_ia()` |
| DLM (Dynamic Load Management) | Divide a potência máxima da estação entre os veículos conectados, priorizando os de menor carga. | `simular_dlm()` e `demo_integrado_sprint3()` |
| Lógica booleana | Recebe solar disponível, demanda, nível da bateria e hora, e decide **qual fonte alimenta cada recarga**. | `decidir_fonte_energia()` |
| Automação | Traduz a decisão em comandos de liga/desliga de cada fonte. | `acionar_automacao()` |
| Armazenamento | Carrega com o excedente solar, descarrega quando o solar não basta e mantém uma reserva mínima. | `atualizar_bateria()` |
| Registro de dados | Grava cada sessão (energia, fonte, comando, custo, CO₂) em CSV. | `exportar_dados_csv()` |
| Dashboard | Consolida energia total, energia solar, receita, CO₂ evitado e nível da bateria. | `dashboard()` |


## 3. Lógica de decisão da fonte de energia

A decisão usa **três variáveis booleanas**:

| Variável | Significado | Condição no código |
|---|---|---|
| **S** | Geração solar suficiente | `energia_solar_kw >= demanda_kw` |
| **B** | Bateria acima do mínimo | `bateria_pct > 25` (`LIMITE_MIN_BATERIA`) |
| **P** | Horário de pico | `18 <= hora <= 22` |

### 3.1 Tabela-verdade

| S | B | P | Solar | Bateria | Rede | Fonte resultante |
|:-:|:-:|:-:|:-:|:-:|:-:|---|
| 0 | 0 | 0 | 0 | 0 | 1 | Rede Normal |
| 0 | 0 | 1 | 0 | 0 | 1 | Rede Pico |
| 0 | 1 | 0 | 0 | 1 | 0 | Bateria |
| 0 | 1 | 1 | 0 | 1 | 0 | Bateria |
| 1 | 0 | 0 | 1 | 0 | 0 | Solar |
| 1 | 0 | 1 | 1 | 0 | 0 | Solar |
| 1 | 1 | 0 | 1 | 0 | 0 | Solar |
| 1 | 1 | 1 | 1 | 0 | 0 | Solar |

### 3.2 Expressões booleanas

- $Solar = S$
- $Bateria = \overline{S} \cdot B$
- $Rede = \overline{S} \cdot \overline{B}$
  - $Rede_{Pico} = \overline{S} \cdot \overline{B} \cdot P$
  - $Rede_{Normal} = \overline{S} \cdot \overline{B} \cdot \overline{P}$

As saídas Solar, Bateria e Rede são **mutuamente exclusivas** (codificação *one-hot*): em qualquer combinação de entradas, exatamente uma fonte fica ativa. A prioridade é sempre a fonte mais sustentável disponível: **Solar > Bateria > Rede**. O horário de pico só influencia a decisão quando a rede é a única opção, pois altera a tarifa aplicada.


## 4. Distribuição de potência (DLM)

O DLM reparte a potência máxima da estação ($P_{max}$ = 100 kW) entre os $n$ veículos conectados, dando **mais potência a quem está com menos carga**:

$$w_i = \max(1,\ 100 - c_i) \qquad\qquad p_i = P_{max} \cdot \frac{w_i}{\sum_{j=1}^{n} w_j}$$

em que $c_i$ é a carga atual do veículo $i$ (%), $w_i$ é o seu peso de prioridade e $p_i$ é a potência alocada (kW). A soma das potências alocadas é igual a $P_{max}$ (a menos de arredondamento), e a potência alocada a cada veículo passa a ser a **demanda** enviada à lógica de decisão da seção 3.

---

## 5. Automação e estado do armazenamento

### 5.1 Comandos de automação

| Fonte decidida | Solar | Bateria | Rede |
|---|:-:|:-:|:-:|
| Solar | ON | OFF | OFF |
| Bateria | OFF | ON | OFF |
| Rede Normal | OFF | OFF | ON (tarifa normal) |
| Rede Pico | OFF | OFF | ON (tarifa de pico) |

### 5.2 Modelo simplificado do armazenamento

Após cada decisão, `atualizar_bateria()` atualiza o nível (%):

- **Fonte Solar com sobra:** o nível sobe de acordo com o excedente (`solar − demanda`), limitado a 100%.
- **Fonte Bateria:** o nível cai `demanda × 1,5`, limitado a 0%.
- **Fonte Rede:** recarga lenta de 0,3 ponto percentual.

O nível de partida é 60%. Ao cair abaixo de 25%, a lógica deixa de usar a bateria e passa para a rede, o que preserva uma reserva mínima.

---

## 6. Justificativa técnica das escolhas

| Escolha | Justificativa |
|---|---|
| **Solar como fonte prioritária** | Menor custo marginal (`R$ 0,05/kWh`, parâmetro do protótipo) e nenhuma emissão de CO₂ na operação. |
| **Armazenamento como segunda opção** | Aproveita o excedente solar quando a geração instantânea não cobre a demanda, reduz a dependência da rede e a pressão no horário de pico. |
| **Rede como último recurso, com tarifa diferenciada** | Garante continuidade do serviço; a tarifa de pico (`R$ 2,25/kWh`) contra a normal (`R$ 1,97/kWh`) torna visível o valor de evitar o horário crítico. |
| **Lógica booleana (tabela-verdade) para a decisão** | Determinística, verificável e de custo computacional mínimo. Pode ser implementada em firmware ou em circuito combinacional, e cada linha da tabela é testável. |
| **DLM proporcional à necessidade de carga** | Evita que a soma das demandas ultrapasse a potência da estação e prioriza os veículos mais descarregados. |
| **Reserva mínima de 25% na bateria** | Protege a vida útil do armazenamento e mantém margem de segurança. |
| **Simulação em software com exportação CSV** | Permite validar a integração e gerar dados de sessão antes de investir em hardware, e o CSV alimenta análises e o dashboard. |

---

## 7. Resultados e dados funcionais

Os resultados abaixo vêm do **modo de demonstração reprodutível** (`--demo`, semente fixa `42`, 5 veículos), executado em dois cenários: **10h (fora do pico)** e **20h (horário de pico)**. Os arquivos completos estão em [`exemplos/`](exemplos/).

### 7.1 Sessões — cenário fora do pico (10h)

| Veículo | Carga | Potência alocada (kW) | Fonte | Valor (R$) | CO₂ evitado (kg) |
|:-:|:-:|:-:|---|:-:|:-:|
| 1 | 18,9% | 23,66 | Solar | 1,18 | 2,839 |
| 2 | 69,3% | 8,96 | Bateria | 0,45 | 1,075 |
| 3 | 29,6% | 20,54 | Bateria | 1,03 | 2,465 |
| 4 | 21,2% | 22,99 | Rede Normal | 45,29 | 0,000 |
| 5 | 18,2% | 23,86 | Rede Normal | 47,00 | 0,000 |

O nível do armazenamento foi de 60% para **22,7%**. Como ficou abaixo do mínimo de 25%, os veículos 4 e 5 passaram a ser atendidos pela rede, exatamente como prevê a tabela-verdade.

### 7.2 Comparação entre os dois cenários

| Indicador | 10h (fora do pico) | 20h (pico) |
|---|:-:|:-:|
| Energia total entregue | 100,01 kWh | 100,01 kWh |
| Energia solar direta | 23,66 kWh | 23,66 kWh |
| Energia da bateria | 29,50 kWh | 29,50 kWh |
| **Parcela renovável** (solar + bateria) | **53,2%** | **53,2%** |
| Energia da rede | 46,85 kWh | 46,85 kWh |
| Fonte da rede | Rede Normal | Rede Pico |
| Receita (custo das sessões) | R$ 94,95 | R$ 108,08 |
| CO₂ evitado | 6,38 kg | 6,38 kg |
| Referência: toda a energia da rede | R$ 197,02 | R$ 225,02 |
| Redução de custo frente à referência | 51,8% | 52,0% |

> A referência considera toda a energia comprada da rede, na tarifa do cenário (100,01 kWh × R$ 1,97 ou × R$ 2,25). Os valores decorrem dos parâmetros do protótipo (seção 10) e de **uma execução simulada**, então servem para demonstrar o funcionamento e não como previsão de economia real.


### 7.3 Dados exportados (CSV)

Cada execução gera `sessoes_recarga.csv` com uma linha por sessão:

| Coluna | Descrição |
|---|---|
| `usuario` | Usuário ou veículo da sessão |
| `energia` | Energia entregue (kWh) |
| `solar` | Energia vinda diretamente do solar (kWh) |
| `rede` | Energia vinda da rede (kWh) |
| `valor` | Valor da sessão (R$) |
| `pagamento` | Forma de pagamento (Pix, Cartão, QR Code ou Simulação) |
| `co2` | CO₂ evitado (kg) |
| `duracao` | Duração da sessão (min) |
| `data` | Data e hora |
| `fonte` | Fonte decidida pela lógica (Solar, Bateria, Rede Normal, Rede Pico) |
| `comando_automacao` | Comando enviado à automação |

---

## 8. Contribuição para sustentabilidade, automação e eficiência

| Tecnologia | Sustentabilidade | Automação inteligente | Eficiência energética |
|---|---|---|---|
| **Geração solar** | Energia limpa, sem emissão na operação; gera o CO₂ evitado registrado por sessão. | Fonte priorizada automaticamente sempre que cobre a demanda. | Uso direto da geração, sem perdas de conversão do armazenamento. |
| **Armazenamento** | Aproveita o excedente renovável em vez de desperdiçá-lo. | Descarrega e recarrega conforme o estado do sistema, com reserva mínima. | Desloca consumo do horário de pico. |
| **DLM** | Reduz picos de demanda e a necessidade de ampliar a infraestrutura. | Reparte a potência entre veículos sem intervenção manual. | Respeita o limite da estação e prioriza quem mais precisa. |
| **Assistente de IA** | Orienta o usuário a recarregar quando há mais energia renovável e menos demanda. | Fornece previsão e recomendação ao sistema. | Incentiva o deslocamento da recarga para fora do pico. |
| **Lógica booleana e automação** | Garante a prioridade Solar > Bateria > Rede. | Decisão e comando em tempo de execução, sem operador. | Minimiza o custo por sessão ao evitar a rede sempre que possível. |
| **Dashboard e CSV** | Torna mensuráveis o CO₂ evitado e a parcela renovável. | Consolida os dados automaticamente. | Base para ajuste fino dos parâmetros. |

---

## 9. Conexão com os conteúdos das disciplinas

**Sistemas Digitais / Arquitetura de Computadores**

- A decisão de fonte é um **circuito combinacional** descrito por **tabela-verdade** com três variáveis de entrada (S, B, P) e três saídas (Solar, Bateria, Rede), simplificado em **expressões booleanas** (seção 3).
- As saídas seguem codificação **one-hot**, típica de sinais de controle, e cada uma corresponde a um comando ON/OFF de automação.
- A lógica pode ser transposta diretamente para portas lógicas (AND, NOT), para um microcontrolador ou para uma simulação de circuito.

**Machine Learning / Modelagem Linear**

- A alocação do DLM é um **modelo linear normalizado**: pesos lineares $w_i = 100 - c_i$ e potências proporcionais a esses pesos (seção 4).
- O assistente de IA está em estágio inicial: hoje faz previsão por faixas de horário, com geração solar simulada. O CSV exportado (energia, fonte, custo, horário) é o insumo para o passo seguinte, ajustar uma **regressão linear** de geração ou demanda em função da hora e substituir as regras fixas.

---

## 10. Premissas, limitações e próximos passos

**Parâmetros do protótipo**

| Constante | Valor | Uso |
|---|:-:|---|
| `PRECO_KWH_NORMAL` | R$ 1,97/kWh | Tarifa da rede fora do pico |
| `PRECO_KWH_PICO` | R$ 2,25/kWh | Tarifa da rede no pico (18h às 22h) |
| `TARIFA_SESSAO` | R$ 0,89 | Taxa fixa por sessão (aplicada nas recargas individuais, opção 2 do menu) |
| `CUSTO_KWH_RENOVAVEL` | R$ 0,05/kWh | Custo de solar e bateria |
| `POTENCIA_MAXIMA` | 100 kW | Potência total da estação no DLM |
| `LIMITE_MIN_BATERIA` | 25% | Reserva mínima do armazenamento |
| `FATOR_CO2_KG_POR_KWH` | 0,12 kg/kWh | CO₂ evitado por kWh renovável |

**Premissas e limitações**

- Geração solar, cargas dos veículos e horário são **simulados** (`random` e relógio do sistema). O modo `--demo` fixa a semente e a hora para reproduzir os resultados.
- O armazenamento é modelado em **percentual**, sem capacidade em kWh; a energia da bateria é tratada como renovável (armazenamento carregado com excedente solar) no cálculo de custo e CO₂.
- Na rodada integrada, as fontes são atribuídas **na ordem de conexão dos veículos** (1 a 5). O DLM define a potência por prioridade de carga, mas a disputa pelo solar e pela bateria segue essa ordem.
- A automação é **simulada por comandos de texto**, sem integração com hardware.

**Próximos passos:** ordenar o atendimento por prioridade do DLM; substituir as regras do assistente por regressão linear treinada com os dados do CSV; integrar os comandos a um controlador real (por exemplo, microcontrolador com relés) ou a protocolos como OCPP.

---


**Menu interativo**

| Opção | Função |
|:-:|---|
| 1 | Cadastrar usuário |
| 2 | Iniciar recarga individual (fonte decidida pela automação, pagamento e pontos) |
| 3 | Consultar pontos de fidelidade |
| 4 | Histórico de sessões |
| 5 | Dashboard |
| 6 | Assistente de IA |
| 7 | Simular DLM |
| 8 | Simulação de carga (energia necessária e autonomia) |
| **9** | **Protótipo integrado (demonstração)** |
| 10 | Exportar dados para CSV |
| 0 | Sair |

O arquivo `sessoes_recarga.csv` é gerado na pasta em que o programa é executado.

---
