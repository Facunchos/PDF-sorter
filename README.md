# 📄 PDF Sorter

Aplicación web para organizar páginas de PDFs de forma manual e interactiva.

## 🚀 Inicio Rápido

### Opción 1: Script de ejecución (Recomendado)

Simplemente ejecuta:
```bash
./run.sh
```

O haz doble clic en el archivo `run.sh` desde el explorador de archivos.

### Opción 2: Manual

```bash
source venv/bin/activate
python app.py
```

Luego abre tu navegador en: **http://localhost:5000**

## 📋 Cómo usar

1. **Coloca tus PDFs** en la carpeta `pdfs/`
2. **Ejecuta la aplicación** con `./run.sh`
3. **Abre el navegador** en http://localhost:5000
4. **Selecciona un PDF** y haz clic en "Run"

### Controles del clasificador

| Botón | Función |
|-------|---------|
| **← Regresar** | Vuelve a la página anterior |
| **Pass** | Ignora la página actual y avanza |
| **Crear nuevo PDF** | Crea un nuevo PDF con esta página como primera |
| **Copiar a...** | Agrega la página al final de un PDF existente |
| **Usar último** | Agrega al último PDF usado (después de primer guardado) |
| **Cancelar** | Termina y muestra resumen |

## 📁 Estructura

```
pdf-sorter/
├── run.sh              # ⚡ Script de ejecución rápida
├── app.py              # Servidor Flask
├── pdfs/               # 📄 Coloca tus PDFs aquí
├── pdfs/nombre-sorted/ # 📁 PDFs organizados (se crean automáticamente)
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   └── sorter.html
└── venv/               # Entorno virtual Python
```

## 🔧 Requisitos

- Python 3.8+
- Flask
- PyMuPDF

Las dependencias se instalan automáticamente con `run.sh`

## 💡 Características

- ✅ Visualiza páginas de PDF como imágenes en el navegador
- ✅ Navega adelante y atrás entre páginas
- ✅ Crea nuevos PDFs con nombres personalizados
- ✅ Agrega páginas a PDFs existentes
- ✅ Validación de nombres de archivo
- ✅ Resumen final con estadísticas
- ✅ Interface oscura y moderna

## ⚠️ Notas

- Los PDFs organizados se guardan en carpetas con sufijo `-sorted`
- Las páginas marcadas con "Pass" se ignoran
- El servidor corre en modo debug para desarrollo local
- Presiona `Ctrl+C` en la terminal para detener el servidor
