# ⚡ Binary Bot Híbrido

Bot automatizado para operações na Deriv, com estratégias inteligentes, gerenciamento de risco, controle de horário e painel em tempo real via Streamlit.

---

## 🚀 Funcionalidades

- 📈 Análise de mercado em tempo real via WebSocket
- 🧠 Estratégia Price Action com detecção de padrões de reversão
- 📊 Cálculo de volatilidade e limiar dinâmico
- 🔁 Gerenciamento de stake via Soros e Martingale Inteligente
- 🧮 Filtro estatístico por taxa de acerto por padrão
- ⏰ Controle de horário de operação com janelas configuráveis
- 🛑 Stop loss e meta de lucro automáticos
- 🧪 Modo simulação para testes sem risco
- 📡 Reconexão automática em caso de queda de WebSocket
- 📋 Painel Streamlit com dados em tempo real: preço, volatilidade, sinal, padrão, lucro

---

## ⚙️ Requisitos do Sistema

Para garantir o funcionamento ideal do bot Megalodon e dos demais módulos, recomenda-se o seguinte ambiente:

### 💻 Sistema Operacional
- Windows 10 ou superior
- Ubuntu 20.04+ ou qualquer distribuição Linux compatível com Python
- macOS 11+ (opcional)

### 🐍 Python
- Versão recomendada: **Python 3.10 a 3.12**
- Verifique com: `python --version`

### 📦 Bibliotecas Python

Instale todas as dependências com:

```bash
pip install -r requirements.txt

ou manualmente

```bash
pip install numpy pandas matplotlib tensorflow websockets

```

## 🧠 Estratégias Implementadas

- **Price Action**: leitura de candles e padrões de reversão (martelo, estrela cadente, engolfo, etc.)
- **Martingale Inteligente**: stake adaptativa com limite de níveis
- **Soros**: aumento progressivo de stake após vitórias
- **Probabilidade Estatística**: só opera padrões com taxa de acerto mínima

---

## ⚙️ Configuração (`config.json`)

```json
{
  "volatility_index": "R_100",
  "stake": 1.00,
  "modo_simulacao": true,
  "meta_lucro_percentual": 0.10,
  "stop_loss_percentual": 0.05,
  "max_operacoes": 20,
  "taxa_minima_acerto": 60,
  "usar_janela_horario": true,
  "janelas_horario": [
    { "inicio": "09:00", "fim": "12:00" },
    { "inicio": "15:00", "fim": "17:00" }
  ]
}

binary_bot_hibrido/
├── core/
│   ├── bot_base.py
│   ├── mercado.py
│   ├── executor.py
│   ├── saldo.py
│   ├── logger.py
│   ├── soros.py
│   ├── desempenho.py
│   └── probabilidade_estatistica.py
├── estrategias/
│   └── martingale_inteligente.py
├── painel/
│   └── streamlit_painel.py
├── dados/
│   └── painel_status.json
├── config.json
└── iniciar_bot.py
```
## Painel Streamlit
```
streamlit run painel/streamlit_painel.py
```
##  Requisitos

Python 3.10+

Bibliotecas: websockets, streamlit, asyncio, statistics, etc.

Instale com:
```
pip install -r requirements.txt

```

## Modo simulacao

Ative no config.json com "modo_simulacao": true para testar estratégias sem enviar ordens reais.

# 🦈 Binary Bot IA — Megalodon Neural Trader

Este projeto é um sistema de bots inteligentes para operar em índices sintéticos da Deriv, incluindo o **bot_megalodon.py**, que utiliza **rede neural** para prever movimentos do mercado com base em indicadores técnicos.

---

## 📁 Estrutura do Projeto

binary_bot_ia/ 
├── bots/ │ 
├── bot_ia.py 
│ └── bot_megalodon.py 
├── core/ │ 
├── modelo_neural.py │ 
├── estatisticas.py │ 
├── painel.py │ 
├── executor.py │ 
├── saldo.py │ 
├── mercado.py │ 
├── logger.py │ 
   └── martingale.py 
├── indicadores/ │ 
   └── indicadores.py 
├── configs/ │ 
   └── config_megalodon.json 
├── iniciar_bot.py 
├── analisar_resultados.py 
├── historico_megalodon.json ← gerado automaticamente


---

## 🚀 Instalação

### 1. Clone o projeto

```bash
git clone https://github.com/seu-usuario/binary_bot_ia.git
cd binary_bot_ia
```
## 2. Crie ambiente virtual (opcional, recomendado)
``` bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS
```
## 3. Instale as dependências
```bash
pip install -r requirements.txt

```
Ou manualmente
```bash
pip install numpy pandas matplotlib tensorflow websockets

```
## 🧠 Executando o bot Megalodon

Configure seu token e parâmetros em configs/config_megalodon.json

Rode o script principal:
```bash
python iniciar_bot.py

```
## 📊 Análise de Desempenho
```bash
python analisar_resultados.py

```
Isso gera gráficos de taxa de acerto por hora e por tipo de entrada, usando os dados do historico_megalodon.json.

## Bibliotecas utilizadas

| 📚 Biblioteca   | 🧠 Função principal                          |
|----------------|----------------------------------------------|
| `numpy`        | Manipulação de arrays e indicadores          |
| `pandas`       | Análise de dados e histórico                 |
| `matplotlib`   | Geração de gráficos                          |
| `tensorflow`   | Rede neural para previsão de mercado         |
| `websockets`   | Comunicação com API da Deriv                 |
| `asyncio`      | Execução assíncrona                          |

## 🧪 Modo Simulação

Para testar sem operar de verdade, defina "modo_simulacao": true no config_megalodon.json. O bot irá simular resultados aleatórios para treinar e testar a IA

## 📈 Evolução do Megalodon
 
 O bot salva cada operação no historico_megalodon.json e re-treina sua rede neural com base nos resultados reais, tornando-se mais preciso com o tempo.