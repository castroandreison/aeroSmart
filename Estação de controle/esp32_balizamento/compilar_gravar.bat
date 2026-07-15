@echo off
chcp 65001 >nul
set PYTHONUTF8=1

set PORTA=COM8
if not "%1"=="" set PORTA=%1

echo Copiando arquivos para C:\esp32_balizamento...
xcopy "%~dp0*.yaml" "C:\esp32_balizamento\" /Y /Q >nul
xcopy "%~dp0*.h" "C:\esp32_balizamento\" /Y /Q >nul

echo Compilando...
python -m esphome compile "C:\esp32_balizamento\esp32_balizamento.yaml"
if %ERRORLEVEL% neq 0 (
    echo ERRO na compilacao.
    pause
    exit /b 1
)

echo.
echo Gravando na porta %PORTA%...
python -m esphome upload "C:\esp32_balizamento\esp32_balizamento.yaml" --device %PORTA%
if %ERRORLEVEL% neq 0 (
    echo ERRO ao gravar.
    pause
    exit /b 1
)

echo.
echo Compilacao e gravacao concluidas com sucesso!
echo.
echo === INSTRUCOES ===
echo 1. Conecte-se ao WiFi "AeroControl" (senha: 123456789)
echo 2. Abra o navegador em http://192.168.4.1
echo 3. Va em Configuracoes ^> Rede e configure seu WiFi/MQTT
echo 4. Clique em "Salvar e Reiniciar"
echo.
echo === MONITOR SERIAL (pressione Ctrl+C para sair) ===
python -m esphome logs "C:\esp32_balizamento\esp32_balizamento.yaml" --device %PORTA%
pause
