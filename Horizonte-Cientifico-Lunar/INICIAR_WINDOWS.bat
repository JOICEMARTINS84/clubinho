@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
 set "PY=py"
) else (
 set "PY=python"
)
echo.
echo HORIZONTE CIENTIFICO - LUA
echo Instalando ou verificando dependencias Python...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
 echo.
 echo Falha ao instalar. Verifique a instalacao do Python e a conexao de internet.
 pause
 exit /b 1
)
echo.
echo Abrindo laboratorio no navegador...
%PY% -m streamlit run streamlit_app.py
pause
