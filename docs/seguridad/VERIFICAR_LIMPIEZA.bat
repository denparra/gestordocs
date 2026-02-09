@echo off
REM Script de verificación post-limpieza (Windows)

echo ================================================
echo VERIFICANDO LIMPIEZA DE .env...
echo ================================================
echo.

echo 1. Verificar historial local:
git log --all --oneline -- .env > temp_check.txt
for %%A in (temp_check.txt) do set size=%%~zA
if %size% EQU 0 (
    echo [OK] .env removido del historial local
) else (
    echo [ERROR] .env todavia esta en el historial local
)
del temp_check.txt
echo.

echo 2. Verificar historial remoto:
git log origin/main --oneline -- .env > temp_check.txt
for %%A in (temp_check.txt) do set size=%%~zA
if %size% EQU 0 (
    echo [OK] .env removido del historial remoto
) else (
    echo [ERROR] .env todavia esta en GitHub
)
del temp_check.txt
echo.

echo 3. Verificar que .env existe en disco:
if exist .env (
    echo [OK] .env existe en disco ^(correcto^)
) else (
    echo [ERROR] .env no existe en disco
)
echo.

echo 4. Verificar .gitignore:
findstr /C:".env" .gitignore >nul 2>&1
if %errorlevel% EQU 0 (
    echo [OK] .env esta en .gitignore
) else (
    echo [ERROR] .env NO esta en .gitignore
)
echo.

echo 5. Verificar git status:
git status --short | findstr .env >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [OK] .env no esta en staging
) else (
    echo [ADVERTENCIA] .env aparece en git status
)
echo.

echo ================================================
echo RESUMEN:
echo Si ves solo [OK], la limpieza fue exitosa
echo ================================================
echo.

pause
