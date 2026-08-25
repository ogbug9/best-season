@echo off
chcp 65001 >nul
setlocal

rem Заливка проекта: коммит + GitHub + Amvera.
rem Просто запусти двойным кликом. Можно передать свой текст коммита:
rem    deploy.bat "phase 4 main page"

cd /d "%~dp0"

set "MSG=%~1"
if "%MSG%"=="" set "MSG=update %date% %time:~0,5%"

echo.
echo ==========================================
echo  Папка: %cd%
echo  Коммит: %MSG%
echo ==========================================
echo.

echo [1/4] Добавляю изменения...
git add -A
if errorlevel 1 goto :err

echo [2/4] Коммит...
git commit -m "%MSG%"
if errorlevel 1 (
  echo.
  echo Коммитить нечего — видимо, изменений нет. Продолжаю с пушем.
  echo.
)

echo [3/4] Пуш на GitHub...
git push origin main
if errorlevel 1 goto :err

echo [4/4] Пуш на Amvera (ветка master — так собирает Amvera)...
git push amvera main:master
if errorlevel 1 goto :err

echo.
echo ==========================================
echo  ГОТОВО. Сборка на Amvera запущена.
echo  Логи: кабинет Amvera - проект best-season - Логи
echo ==========================================
echo.
pause
exit /b 0

:err
echo.
echo ==========================================
echo  ОШИБКА. Прочитай текст выше и скинь его в чат.
echo ==========================================
echo.
pause
exit /b 1
