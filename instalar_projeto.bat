@echo off
SETLOCAL

echo 🔧 Iniciando setup do projeto Binary Bot IA...

REM Verifica se o ambiente virtual existe
IF NOT EXIST ".venv" (
    echo 📦 Criando ambiente virtual...
    python -m venv .venv
)

REM Ativa o ambiente virtual
CALL .venv\Scripts\activate

REM Atualiza pip e instala dependências
echo 📚 Instalando dependências do requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt

REM Verifica se a DLL do TensorFlow está presente
echo 🔍 Verificando dependência do TensorFlow...
where msvcp140_1.dll >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    echo ✅ DLL 'msvcp140_1.dll' encontrada. TensorFlow deve funcionar corretamente.
) ELSE (
    echo ❌ DLL 'msvcp140_1.dll' não encontrada.
    echo ⚠️ Instale o Microsoft Visual C++ Redistributable: https://support.microsoft.com/help/2977003
)

echo ✅ Setup concluído com sucesso!
ENDLOCAL
pause
