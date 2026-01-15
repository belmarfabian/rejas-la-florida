#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SNAP TO ROAD - Ajustar puntos a la red vial
================================================================================

Este script ajusta las coordenadas de rejas/puntos para que queden
exactamente sobre las calles mas cercanas usando datos de OpenStreetMap.

USO:
    python snap_to_road.py

ENTRADA:
    - Archivo Excel con columnas 'lat' y 'lon' (o 'cord' con formato "lat, lon")

SALIDA:
    - Archivo Excel con coordenadas ajustadas
    - Columnas adicionales: lat_original, lon_original, dist_ajuste_m

REQUISITOS:
    pip install pandas openpyxl osmnx scipy numpy

AUTOR: Proyecto Rejas La Florida
FECHA: Diciembre 2025
================================================================================
"""

import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import os

# Intentar importar osmnx
try:
    import osmnx as ox
except ImportError:
    print("ERROR: Falta instalar osmnx")
    print("Ejecuta: pip install osmnx")
    exit(1)


def parse_coordenadas(cord_str):
    """Extrae lat, lon de un string con formato 'lat, lon'"""
    try:
        parts = str(cord_str).split(',')
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return lat, lon
    except:
        return None, None


def snap_to_road(input_file, output_file=None, lugar="La Florida, Santiago, Chile"):
    """
    Ajusta los puntos de un archivo Excel a la red vial mas cercana.

    Parametros:
    -----------
    input_file : str
        Ruta al archivo Excel de entrada
    output_file : str, opcional
        Ruta al archivo de salida (si no se especifica, agrega '_snapped')
    lugar : str
        Nombre del lugar para descargar la red vial de OpenStreetMap

    Retorna:
    --------
    DataFrame con las coordenadas ajustadas
    """

    print("="*60)
    print("SNAP TO ROAD - Ajustar puntos a la red vial")
    print("="*60)

    # Generar nombre de salida si no se especifica
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_snapped{ext}"

    # 1. Cargar datos
    print(f"\n[1/4] Cargando datos de: {input_file}")
    df = pd.read_excel(input_file)
    print(f"      {len(df)} puntos encontrados")

    # Verificar si tiene lat/lon o cord
    if 'lat' not in df.columns or 'lon' not in df.columns:
        if 'cord' in df.columns:
            print("      Extrayendo lat/lon de columna 'cord'...")
            coords = df['cord'].apply(parse_coordenadas)
            df['lat'] = coords.apply(lambda x: x[0])
            df['lon'] = coords.apply(lambda x: x[1])
        elif 'Coordenadas' in df.columns:
            print("      Extrayendo lat/lon de columna 'Coordenadas'...")
            coords = df['Coordenadas'].apply(parse_coordenadas)
            df['lat'] = coords.apply(lambda x: x[0])
            df['lon'] = coords.apply(lambda x: x[1])
        else:
            print("ERROR: No se encontraron columnas de coordenadas")
            print("       El archivo debe tener 'lat'/'lon' o 'cord' o 'Coordenadas'")
            return None

    # Eliminar filas sin coordenadas
    df = df.dropna(subset=['lat', 'lon'])
    print(f"      {len(df)} puntos con coordenadas validas")

    # 2. Descargar red vial
    print(f"\n[2/4] Descargando red vial de: {lugar}")
    print("      (esto puede tomar 1-2 minutos la primera vez)")

    try:
        G = ox.graph_from_place(lugar, network_type='drive', simplify=True)
    except:
        print("      No se pudo descargar por nombre, usando area centrada en los datos...")
        centro_lat = df['lat'].mean()
        centro_lon = df['lon'].mean()
        G = ox.graph_from_point((centro_lat, centro_lon), dist=5000,
                                 network_type='drive', simplify=True)

    print(f"      Red descargada: {len(G.nodes)} nodos, {len(G.edges)} aristas")

    # 3. Preparar busqueda
    print("\n[3/4] Preparando algoritmo de busqueda...")
    nodes = list(G.nodes(data=True))
    node_coords = np.array([[data['y'], data['x']] for _, data in nodes])
    tree = cKDTree(node_coords)

    # 4. Ajustar puntos
    print(f"\n[4/4] Ajustando {len(df)} puntos a la red vial...")

    new_lats = []
    new_lons = []
    distances = []

    for idx, row in df.iterrows():
        # Buscar nodo mas cercano
        dist, i = tree.query([row['lat'], row['lon']])

        # Guardar nueva posicion
        new_lats.append(node_coords[i][0])
        new_lons.append(node_coords[i][1])

        # Calcular distancia en metros (aproximado)
        dist_metros = dist * 111000  # 1 grado ~ 111km
        distances.append(dist_metros)

        # Mostrar progreso
        if (idx + 1) % 500 == 0:
            print(f"      {idx + 1}/{len(df)} procesados...")

    # Agregar columnas
    df['lat_original'] = df['lat']
    df['lon_original'] = df['lon']
    df['lat'] = new_lats
    df['lon'] = new_lons
    df['dist_ajuste_m'] = distances

    # Guardar
    df.to_excel(output_file, index=False)

    # Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print(f"  Puntos procesados: {len(df)}")
    print(f"  Ajuste promedio:   {np.mean(distances):.1f} metros")
    print(f"  Ajuste maximo:     {np.max(distances):.1f} metros")
    print(f"  Ajuste minimo:     {np.min(distances):.1f} metros")
    print(f"  Puntos con >50m:   {sum(1 for d in distances if d > 50)}")
    print(f"\n  Guardado en: {output_file}")
    print("="*60)

    return df


# ==============================================================================
# EJECUTAR
# ==============================================================================
if __name__ == "__main__":

    # CONFIGURACION - Modificar segun necesidad
    # ==========================================

    ARCHIVO_ENTRADA = "../03_datos_procesados/Base_Combinada.xlsx"
    ARCHIVO_SALIDA = "../03_datos_procesados/Base_Combinada_Snapped.xlsx"
    LUGAR = "La Florida, Santiago, Chile"

    # ==========================================

    # Ejecutar
    resultado = snap_to_road(
        input_file=ARCHIVO_ENTRADA,
        output_file=ARCHIVO_SALIDA,
        lugar=LUGAR
    )

    if resultado is not None:
        print("\n[OK] Proceso completado exitosamente!")
        print("\nColumnas en el archivo de salida:")
        print("  - lat, lon: Coordenadas ajustadas a la calle")
        print("  - lat_original, lon_original: Coordenadas originales")
        print("  - dist_ajuste_m: Distancia del ajuste en metros")
