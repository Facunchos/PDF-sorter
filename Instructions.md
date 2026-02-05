# PDF Sorter - Instrucciones para Copilot

## Descripción del Proyecto

PDF Sorter es una aplicación web Flask que permite clasificar páginas de PDFs. El usuario puede ver cada página de un PDF y decidir a qué nuevo PDF debe pertenecer, creando así documentos organizados a partir de un archivo fuente grande.

## Estructura del Proyecto

```
pdf-sorter/
├── app.py              # Servidor Flask con todas las rutas API
├── requirements.txt    # Dependencias Python (Flask, PyMuPDF)
├── run.sh             # Script para ejecutar la aplicación
├── README.md          # Documentación general
├── Instructions.md    # Este archivo (instrucciones para Copilot)
├── pdfs/              # Carpeta donde se almacenan los PDFs
│   └── *-sorted/      # Subcarpetas con PDFs clasificados
├── static/
│   └── style.css      # Estilos de la aplicación (tema oscuro)
└── templates/
    ├── index.html     # Página principal con tabla de PDFs
    └── sorter.html    # Página del clasificador de páginas
```

## Flujo de Uso

1. **Página Principal** (`/`): Muestra una tabla con todos los PDFs en la carpeta `pdfs/`
   - Subir nuevos PDFs con el botón "Subir PDF"
   - Ver cantidad de páginas de cada PDF
   - Abrir PDF en el navegador
   - Ejecutar el sorter desde una página específica
   - Descargar o eliminar PDFs

2. **Página Sorter** (`/sorter/<filename>`): Clasificador de páginas
   - Muestra una página a la vez como imagen
   - El usuario decide qué hacer con cada página:
     - **Regresar**: Vuelve a la página anterior
     - **Pass**: Ignora la página actual
     - **Crear nuevo PDF**: Crea un PDF nuevo con esta página
     - **Copiar a...**: Agrega la página a un PDF existente
     - **Usar último**: Agrega la página al último PDF usado

## Rutas de la API (app.py)

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/` | GET | Página principal con lista de PDFs |
| `/upload` | POST | Sube un PDF a la carpeta pdfs/ |
| `/download/<filename>` | GET | Descarga un PDF |
| `/delete/<filename>` | DELETE | Elimina un PDF (y opcionalmente su carpeta -sorted) |
| `/open/<filename>` | GET | Sirve el PDF para visualización en navegador |
| `/page/<filename>/<page_num>` | GET | Renderiza una página como imagen PNG |
| `/page-count/<filename>` | GET | Obtiene el número total de páginas |
| `/sorter/<filename>` | GET | Página del clasificador (acepta `?start=N`) |
| `/list-sorted/<filename>` | GET | Lista PDFs en la carpeta sorted |
| `/check-name/<filename>` | POST | Valida nombre de nuevo PDF |
| `/create-pdf/<filename>` | POST | Crea nuevo PDF con una página |
| `/append-to-pdf/<filename>` | POST | Agrega página a PDF existente |

## Atajos de Teclado (sorter.html)

### Sin Modal Abierto
| Tecla | Acción |
|-------|--------|
| `1` | Regresar a página anterior |
| `2` | Pass (ignorar página) |
| `3` | Crear nuevo PDF |
| `4` | Copiar a PDF existente |
| `5` | Usar último PDF |
| `G` | Saltar a página específica |

### Modal "Copiar a..."
| Tecla | Acción |
|-------|--------|
| `↑` / `↓` | Navegar por la lista de PDFs |
| `1-9` | Selección rápida por número |
| `Enter` | Confirmar selección |
| `Escape` | Cerrar modal |

### Otros Modales
| Tecla | Acción |
|-------|--------|
| `Enter` | Confirmar |
| `Escape` | Cancelar/Cerrar |

## Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **PDF Processing**: PyMuPDF (fitz)
- **Frontend**: HTML, CSS, JavaScript vanilla
- **Estilos**: CSS custom con tema oscuro (#1a1a2e base, #00d4ff accent)

## Carpetas Sorted

Cuando se clasifican páginas de un PDF (ej: `documento.pdf`), los nuevos PDFs se guardan en una carpeta llamada `documento-sorted/` dentro de `pdfs/`.

## Estado de la Aplicación (JavaScript)

El objeto `state` en sorter.html mantiene:
```javascript
{
    filename: "...",          // Nombre del PDF actual
    currentPage: N,           // Página actual
    totalPages: N,            // Total de páginas
    history: [],              // Stack para botón regresar
    lastPdf: null,            // Último PDF usado (para "Usar último")
    lastVisitedPage: null,    // Última página visitada
    selectedCopyTarget: null, // PDF seleccionado en modal copiar
    copyTargetIndex: -1,      // Índice en la lista de copiar
    stats: {                  // Estadísticas de la sesión
        created: 0,
        pagesAdded: 0,
        skipped: 0,
        pdfDetails: {}
    }
}
```

## Notas para Desarrollo

- Los PDFs se renderizan con zoom 2x para mejor calidad
- Los nombres de archivo se sanitizan para evitar caracteres problemáticos
- El modal de confirmación al eliminar pregunta si también eliminar la carpeta -sorted
- La página actual se puede clickear para saltar a otra página
- Se muestra la última página visitada en el header
