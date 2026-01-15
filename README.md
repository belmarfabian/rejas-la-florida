# Mapa de Rejas - La Florida

Proyecto para analizar la fragmentacion vial causada por rejas en la comuna de La Florida, Santiago, Chile.

---

## Estructura del Proyecto

```
La Florida/
│
├── 00_archivo_portones/          # ARCHIVO (Trabajo anterior de portones)
│   ├── datos_originales/         # Decretos y datos de portones
│   ├── documentos/               # PDFs oficiales
│   └── README_ARCHIVO.md
│
├── 01_datos_originales/          # DATOS DE ENTRADA
│   ├── Rejas_Fabian.xlsx         # Datos recopilados por Fabian
│   ├── Rejas_Thomas.xlsx         # Datos recopilados por Thomas
│   ├── Rejas_Thomas_preliminar.xlsx
│   ├── Direcciones_Nicolas.xlsx  # Datos recopilados por Nicolas
│   ├── Direcciones_LaFlorida.xlsx
│   └── Calles_Abiertas.xlsx      # Datos de calles abiertas
│
├── 02_scripts/                   # SCRIPTS Y NOTEBOOKS
│   ├── mapa_rejas_SIMPLE.py      # Script principal de mapas
│   ├── mapa_rejas.py             # Script alternativo
│   ├── agregar_direcciones.py    # Utilidad para geocoding
│   └── Tutorial_Mapas_Rejas.ipynb
│
├── 03_datos_procesados/          # DATOS COMBINADOS/PROCESADOS
│   ├── Base_Combinada_Fabian_Thomas_Nicolas.xlsx
│   └── Rejas_con_direcciones.xlsx
│
├── 04_mapas_html/                # MAPAS INTERACTIVOS
│   ├── 1a_Puntos_Simple.html
│   ├── 1b_Puntos_Combinado.html
│   ├── 2a_Heatmap.html
│   ├── 2b_Voronoi.html
│   ├── 2c_Hexagonal.html
│   ├── 3_Privacion_Vial_POIs.html
│   ├── 4_Fragmentacion_Red.html
│   ├── 5_Rejas_Criticas.html
│   └── [mapas legacy]
│
├── 05_analisis/                  # RESULTADOS DE ANALISIS
│   ├── 1_percolacion.png         # Grafico de percolacion
│   ├── 2_contagio.png            # Grafico de contagio
│   ├── 3_resiliencia.png         # Grafico de resiliencia
│   ├── accesibilidad_resultados.xlsx
│   └── rejas_criticas.xlsx
│
├── 06_reporte/                   # REPORTE FINAL
│   ├── Reporte_Fragmentacion_Vial_LaFlorida.html
│   └── Reporte_Fragmentacion_Vial_LaFlorida.md
│
├── cache/                        # Cache de geocoding
└── README.md                     # Este archivo
```

> **Nota**: La carpeta `00_archivo_portones/` contiene el trabajo previo de portones en pasajes.
> Se mantiene como respaldo historico.

---

## Inicio Rapido

### Instalar dependencias

```bash
pip install pandas folium openpyxl networkx scipy
```

### Ver resultados

Los mapas interactivos estan en `04_mapas_html/`. Abrir cualquier archivo `.html` en el navegador.

---

## Descripcion de Carpetas

### 01_datos_originales/
Datos crudos recopilados por cada colaborador:
- **Rejas_Fabian.xlsx** - 176 registros originales
- **Rejas_Thomas.xlsx** - Datos adicionales de Thomas
- **Direcciones_Nicolas.xlsx** - Direcciones de Nicolas
- **Calles_Abiertas.xlsx** - Registro de calles abiertas

### 03_datos_procesados/
- **Base_Combinada_Fabian_Thomas_Nicolas.xlsx** - Fusion de todos los datos
- **Rejas_con_direcciones.xlsx** - Rejas geocodificadas

### 04_mapas_html/
Mapas interactivos generados:
| Mapa | Descripcion |
|------|-------------|
| 1a_Puntos_Simple.html | Puntos basicos |
| 1b_Puntos_Combinado.html | Todos los datos combinados |
| 2a_Heatmap.html | Mapa de calor |
| 2b_Voronoi.html | Diagrama de Voronoi |
| 2c_Hexagonal.html | Agregacion hexagonal |
| 3_Privacion_Vial_POIs.html | Accesibilidad a servicios |
| 4_Fragmentacion_Red.html | Analisis de red vial |
| 5_Rejas_Criticas.html | Rejas mas criticas |

### 05_analisis/
Resultados del analisis de fragmentacion:
- Graficos de percolacion, contagio y resiliencia
- Resultados de accesibilidad en Excel
- Lista de rejas criticas

### 06_reporte/
Reporte final del estudio en formato HTML y Markdown.

---

## Requisitos

- Python 3.x
- pandas, folium, openpyxl, networkx, scipy

---

## Colaboradores

- Fabian
- Thomas Villaseca Arroyo
- Nicolas Covarrubias

---

**Ultima actualizacion**: Diciembre 2025
**Version**: 4.0
