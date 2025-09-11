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