# 🤖 Binary Bot Híbrido

Bot de operações automatizadas na Deriv usando WebSocket, RSI, Bollinger Bands e gerenciamento SorosGale com controle de saldo.

## 🚀 Funcionalidades

- Conexão com Deriv via WebSocket
- Estratégia RSI + Bollinger Bands
- Execução de ordens CALL/PUT
- Gerenciamento SorosGale
- Controle de saldo dinâmico
- Reconexão automática
- Logs de operação

## 🛠️ Requisitos

- Python 3.11+
- Conta na Deriv (token de API)
- Biblioteca `websockets`

```bash
pip install websockets
```
##  Execução  
```bash
python main.py
``` 
## 📘 Estratégias Disponíveis

Este projeto oferece múltiplas estratégias de operação em opções binárias, cada uma com lógica técnica distinta e aplicação ideal. Abaixo estão os detalhes de cada uma:

| Estratégia               | Descrição Técnica                                                                 | Indicadores Usados                     | Aplicação Ideal                         |
|--------------------------|------------------------------------------------------------------------------------|----------------------------------------|------------------------------------------|
| **bollinger_volatilidade** | Detecta rompimentos das bandas de Bollinger com volatilidade acima de um limiar. | Bollinger Bands + Volatilidade         | Mercados com explosões de preço          |
| **mm_rsi**                | Cruza médias móveis com confirmação de RSI para entrada mais segura.             | Média Móvel Curta + Longa + RSI        | Tendências suaves com reversões claras   |
| **rsi_bollinger**         | Combina RSI extremo com rompimento das bandas para validar sobrecompra/sobrevenda. | RSI + Bollinger Bands                  | Reversões técnicas em zonas de exaustão  |
| **price_action**          | Analisa o formato das velas (corpo, sombra) para detectar padrões de rejeição.   | Candlestick + Proporção de corpo/sombra | Mercados laterais ou com rejeições visuais |
| **reversao_tendencia**    | Detecta reversões com base em mudança de direção + RSI + sensibilidade de variação. | RSI + Direção de preço + Sensibilidade | Fim de tendência ou início de correção   |

---

Cada estratégia pode ser ativada individualmente via o script `iniciar_bot.py`, utilizando seu respectivo arquivo de configuração localizado na pasta `configs/`.

Exemplo de uso:

```bash
python iniciar_bot.py rsi_bollinger