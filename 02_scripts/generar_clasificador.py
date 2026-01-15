#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera el Clasificador Interactivo con los datos de intersecciones faltantes.
"""

import pandas as pd
import osmnx as ox
from scipy.spatial import cKDTree
import json

print("="*70)
print("GENERANDO CLASIFICADOR INTERACTIVO")
print("="*70)

# 1. Cargar datos clasificados
print("\n[1/4] Cargando datos existentes...")
df = pd.read_excel('../03_datos_procesados/Base_Combinada_Snapped_v2.xlsx')
print(f"      {len(df)} puntos clasificados")

# 2. Descargar red vial
print("\n[2/4] Descargando red vial de La Florida...")
G = ox.graph_from_place("La Florida, Santiago, Chile", network_type='all', simplify=True)
print(f"      {len(G.nodes)} nodos, {len(G.edges)} aristas")

# 3. Identificar intersecciones residenciales faltantes
print("\n[3/4] Identificando intersecciones sin clasificar...")

tipos_residenciales = {'residential', 'living_street'}
nodos_residenciales = set()

for u, v, data in G.edges(data=True):
    highway = data.get('highway', '')
    tipos = set(highway) if isinstance(highway, list) else {highway}
    if tipos & tipos_residenciales:
        nodos_residenciales.add(u)
        nodos_residenciales.add(v)

# Filtrar intersecciones (grado > 1)
intersecciones = []
for node in nodos_residenciales:
    if G.degree(node) > 1:
        data = G.nodes[node]
        intersecciones.append({
            'lat': data['y'],
            'lon': data['x'],
            'grado': G.degree(node)
        })

print(f"      {len(intersecciones)} intersecciones residenciales")

# Filtrar las que ya tienen clasificación
tree = cKDTree(df[['lat', 'lon']].values)
umbral = 30 / 111000

faltantes = []
for inter in intersecciones:
    dist, _ = tree.query([inter['lat'], inter['lon']])
    if dist > umbral:
        faltantes.append(inter)

print(f"      {len(faltantes)} sin clasificar")

# 4. Generar HTML
print("\n[4/4] Generando HTML...")

# Leer template
with open('../04_mapas_html/Clasificador_Interactivo.html', 'r', encoding='utf-8') as f:
    template = f.read()

# Calcular centro
centro_lat = sum(i['lat'] for i in faltantes) / len(faltantes)
centro_lon = sum(i['lon'] for i in faltantes) / len(faltantes)

# Generar datos JavaScript
datos_js = json.dumps(faltantes, indent=12)

# Reemplazar placeholder y centro
html_final = template.replace(
    '// DATOS_PLACEHOLDER - Será reemplazado por Python',
    datos_js[1:-1]  # Quitar corchetes externos
)

html_final = html_final.replace(
    "centro: [-33.52, -70.60]",
    f"centro: [{centro_lat:.6f}, {centro_lon:.6f}]"
)

# Guardar
output_path = '../04_mapas_html/Clasificador_Rejas.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_final)

print(f"\n{'='*70}")
print("CLASIFICADOR GENERADO")
print("="*70)
print(f"  Archivo: {output_path}")
print(f"  Puntos a clasificar: {len(faltantes)}")
print(f"\n  Instrucciones:")
print(f"  1. Abrir el archivo HTML en un navegador")
print(f"  2. Hacer clic en los puntos naranjas")
print(f"  3. Seleccionar si está cerrada o abierta")
print(f"  4. Al terminar, exportar las clasificaciones")
print("="*70)
