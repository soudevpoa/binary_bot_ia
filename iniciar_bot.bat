@echo off
SETLOCAL

REM Ativa o ambiente virtual
CALL .venv\Scripts\activate

REM Menu de seleção
echo ================================
echo Iniciar Bot Inteligente
echo ================================
echo [1] Bot Megalodon
echo [2] Bot IA
echo [3] Painel Streamlit
echo [4] Bot MM + RSI
echo [5] Bot Media Movel
echo [6] Bot Price Action
echo [7] Bot Reversao de Tendencia
echo [8] Bot RSI + Bollinger
echo [0] Cancelar
echo ================================
set /p escolha=Escolha uma opcao: 

IF "%escolha%"=="1" (
    echo 🚀 Iniciando Bot Megalodon...
    python iniciar_bot.py
    GOTO :EOF
)

IF "%escolha%"=="2" (
    echo 🚀 Iniciando Bot IA...
    python iniciar_bot.py
    GOTO :EOF
)

IF "%escolha%"=="3" (
    echo 🌐 Iniciando Painel Streamlit...
    streamlit run painel.py --server.port 8501 --server.headless true
    GOTO :EOF
)

IF "%escolha%"=="4" (
    echo 🚀 Iniciando Bot MM + RSI...
    python iniciar_mm_rsi.py
    GOTO :EOF
)

IF "%escolha%"=="5" (
    echo 🚀 Iniciando Bot Média Móvel...
    python iniciar_mm.py
    GOTO :EOF
)

IF "%escolha%"=="6" (
    echo 🚀 Iniciando Bot Price Action...
    python iniciar_price_action.py
    GOTO :EOF
)

IF "%escolha%"=="7" (
    echo 🔄 Iniciando Bot Reversão de Tendência...
    python iniciar_reversao.py
    GOTO :EOF
)

IF "%escolha%"=="8" (
    echo 📊 Iniciando Bot RSI + Bollinger...
    python iniciar_rsi.py
    GOTO :EOF
)

IF "%escolha%"=="0" (
    echo ❌ Cancelado.
    GOTO :EOF
)

echo ⚠️ Opção inválida.
ENDLOCAL
pause
