#!/bin/bash

# Script para ejecutar PDF Sorter

# Obtener directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "⚠️  No se encontró el entorno virtual. Creándolo..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Instalando dependencias..."
    pip install Flask PyMuPDF
else
    source venv/bin/activate
fi

# Verificar si existe la carpeta pdfs
if [ ! -d "pdfs" ]; then
    mkdir pdfs
    echo "📁 Carpeta 'pdfs' creada"
fi

# Ejecutar la aplicación
echo ""
echo "🚀 Iniciando PDF Sorter..."
echo "📄 Abre tu navegador en: http://localhost:5000"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

python app.py
