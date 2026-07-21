@echo off
chcp 65001 >nul
set PYTHONUTF8=1

set ORIGEM=%~dp0
set DESTINO=C:\esp32_balizamento
set FIRMWARE_DIR=%ORIGEM%firmware
set BUILD_DIR=%DESTINO%\.esphome\build\balizamento-pista\.pioenvs\balizamento-pista

echo Copiando arquivos para %DESTINO%...
xcopy "%ORIGEM%*.yaml" "%DESTINO%\" /Y /Q >nul
xcopy "%ORIGEM%*.h" "%DESTINO%\" /Y /Q >nul

echo Compilando...
python -m esphome compile "%DESTINO%\esp32_balizamento.yaml"
if %ERRORLEVEL% neq 0 (
    echo ERRO na compilacao.
    pause
    exit /b 1
)

echo.
echo Copiando firmware para %FIRMWARE_DIR%...
copy /Y "%BUILD_DIR%\firmware.ota.bin" "%FIRMWARE_DIR%\latest.ota.bin" >nul
copy /Y "%BUILD_DIR%\firmware.bin" "%FIRMWARE_DIR%\latest.bin" >nul

REM Gerar MD5 do firmware.ota.bin
certutil -hashfile "%FIRMWARE_DIR%\latest.ota.bin" MD5 2>nul | findstr /v "MD5" > "%FIRMWARE_DIR%\latest.md5"

REM Atualizar version.json
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set DT=%%I
if defined DT (
    set ANO=%DT:~0,4%
    set MES=%DT:~4,2%
    set DIA=%DT:~6,2%
    set HORA=%DT:~8,2%
    set MIN=%DT:~10,2%
    set SEG=%DT:~12,2%
    set TIMESTAMP=%ANO%-%MES%-%DIA%T%HORA%:%MIN%:%SEG%
) else (
    set TIMESTAMP=2026-01-01T00:00:00
)

(for %%a in (
"{"
"    ""min_esphome_version"": ""2026.6.5"","
"    ""esp_platform"": ""ESP32"","
"    ""version"": ""2.0.6"","
"    ""build_time"": ""%TIMESTAMP%"","
"    ""project"": ""AeroControl Balizamento""
"}"
) do @echo %%~a) > "%FIRMWARE_DIR%\version.json"

echo.
echo Compilacao concluida com sucesso!
echo Firmware OTA: %FIRMWARE_DIR%\latest.ota.bin
echo MD5: %FIRMWARE_DIR%\latest.md5
echo.
pause
