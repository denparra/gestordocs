#!/bin/bash

# Script de verificación post-limpieza

echo "🔍 VERIFICANDO LIMPIEZA DE .env..."
echo ""

echo "1️⃣ Verificar historial local:"
git log --all --oneline -- .env
if [ $? -eq 0 ] && [ -z "$(git log --all --oneline -- .env)" ]; then
    echo "✅ .env removido del historial local"
else
    echo "❌ .env todavía está en el historial local"
fi
echo ""

echo "2️⃣ Verificar historial remoto:"
git log origin/main --oneline -- .env
if [ $? -eq 0 ] && [ -z "$(git log origin/main --oneline -- .env)" ]; then
    echo "✅ .env removido del historial remoto"
else
    echo "❌ .env todavía está en GitHub"
fi
echo ""

echo "3️⃣ Verificar que .env existe en disco (debe existir):"
if [ -f .env ]; then
    echo "✅ .env existe en disco (correcto)"
else
    echo "❌ .env no existe en disco (problema)"
fi
echo ""

echo "4️⃣ Verificar .gitignore:"
if grep -q "^\.env$" .gitignore; then
    echo "✅ .env está en .gitignore"
else
    echo "❌ .env NO está en .gitignore"
fi
echo ""

echo "5️⃣ Verificar git status:"
git status --short | grep .env
if [ $? -ne 0 ]; then
    echo "✅ .env no está en staging"
else
    echo "⚠️ .env aparece en git status"
fi

echo ""
echo "========================================="
echo "RESUMEN:"
echo "Si ves solo ✅, la limpieza fue exitosa"
echo "========================================="
