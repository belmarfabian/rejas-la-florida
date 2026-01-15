# Mapa de Rejas - La Florida

Proyecto para analizar la fragmentación vial causada por rejas en la comuna de La Florida, Santiago, Chile.

---

## Clasificador Interactivo

**URL:** https://belmarfabian.github.io/rejas-la-florida/04_mapas_html/Clasificador_Rejas.html

### Estado Actual
| Métrica | Valor |
|---------|-------|
| Total puntos | 15,091 |
| Ya clasificados | 8,457 (56%) |
| Pendientes | 6,634 (44%) |

### Lógica de Selección de Puntos

**Incluye:** Todos los nodos de OSM excepto cruces de calles principales.

**Excluye:** Nodos donde SOLO se conectan calles principales (primary, secondary, tertiary, motorway).

```python
# Tipos excluidos (cruces de avenidas)
principales = {'primary', 'secondary', 'tertiary', 'primary_link',
               'secondary_link', 'tertiary_link', 'motorway', 'motorway_link'}

# Si el nodo SOLO tiene estos tipos, se excluye
# Si tiene al menos un tipo "cerrable", se incluye
```

### Cómo Modificar la Lógica

Para cambiar qué puntos se muestran, editar `02_scripts/generar_clasificador_todos.py`:

```python
# OPCIÓN 1: Solo inicios de pasaje (donde residencial conecta con principal)
# Cambiar la lógica a: nodos donde residential/living_street conecta con primary/secondary/tertiary

# OPCIÓN 2: Solo no-cruces (1-2 vecinos)
# Filtrar: len(set(G.neighbors(node))) <= 2

# OPCIÓN 3: Solo calles residenciales
# Filtrar: nodos con al menos 1 conexión a residential o living_street
```

Luego ejecutar:
```bash
cd 02_scripts
python generar_clasificador_todos.py
```

### Análisis de Puntos Clasificados

Donde están los 5,709 puntos ya clasificados:
- **56%** en cruces de 3 calles (T)
- **36%** en cruces de 4 calles (X)
- **7%** en puntos de 1-2 conexiones (inicios/finales)

---

## Estructura del Proyecto

```
La Florida/
├── 01_datos_originales/          # Datos de entrada
│   ├── Rejas_Nicolas.xlsx        # 1,923 puntos
│   ├── Rejas_Thomas.xlsx         # 1,940 puntos
│   └── Calles_Abiertas.xlsx      # 1,846 puntos
│
├── 02_scripts/                   # Scripts
│   ├── generar_clasificador_todos.py  # Genera el clasificador
│   ├── Procesamiento_Rejas_LaFlorida.ipynb  # Notebook completo
│   └── snap_to_road.py           # Ajuste a calles OSM
│
├── 03_datos_procesados/          # Datos procesados
│   ├── Base_Combinada.xlsx       # 5,709 puntos mergeados
│   └── Base_Combinada_Snapped_v2.xlsx  # Ajustados a calles
│
├── 04_mapas_html/                # Mapas interactivos
│   ├── Clasificador_Rejas.html   # Clasificador principal
│   ├── 1_Mapa_Rejas_Snapped_v2.html
│   └── 5_Inicios_Faltantes.html
│
├── 05_analisis/                  # Resultados
└── 06_reporte/                   # Reporte final
```

---

## Tipos de Calle en OSM (La Florida)

| Tipo | Cantidad | Descripción |
|------|----------|-------------|
| living_street | 11,494 | Pasajes/calles de convivencia |
| residential | 9,986 | Calles residenciales |
| footway | 9,926 | Senderos peatonales |
| tertiary | 3,913 | Calles terciarias |
| service | 3,913 | Calles de servicio |
| secondary | 2,315 | Calles secundarias |
| primary | 657 | Calles principales |

---

## Requisitos

```bash
pip install pandas openpyxl folium osmnx scipy shapely
```

---

## Colaboradores

- Fabián Belmar
- Thomas Villaseca Arroyo
- Nicolás Covarrubias

---

**Última actualización:** Enero 2026
**Repo:** https://github.com/belmarfabian/rejas-la-florida
