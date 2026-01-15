#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MAPA INTERACTIVO DE REJAS - REGIÓN METROPOLITANA
================================================================================

DESCRIPCIÓN:
Este script genera un mapa interactivo que muestra todas las rejas de la región.
Las rejas tienen dos estados:
  - Estado 1 (ABIERTA): Se muestra en ROJO
  - Estado 0 (CERRADA): Se muestra con GRADIENTE de colores por año de cierre
                        (oscuro = antiguo, claro = reciente)

ENTRADA:
  - Archivo: 01_datos_originales/Rejas.xlsx
  - Columnas necesarias:
    * cord: coordenadas en formato "latitud, longitud"
    * estado: 1 (abierta) o 0 (cerrada)
    * año: año de cierre

SALIDA:
  - Archivo: 04_mapas_html/Mapa_Rejas_RegionMetropolitana.html
  - Mapa HTML interactivo con folium

AUTOR: Análisis Región Metropolitana
FECHA: Noviembre 2025
================================================================================
"""

import pandas as pd
import folium
from folium import plugins


def calcular_color_gradiente(año, año_min, año_max):
    """
    Calcula el color para una reja cerrada basado en su año de cierre.

    Parámetros:
    -----------
    año : int
        Año de cierre de la reja
    año_min : int
        Año más antiguo en el dataset
    año_max : int
        Año más reciente en el dataset

    Retorna:
    --------
    str
        Color en formato hexadecimal (ej: '#1a2b3c')

    Lógica:
    -------
    - Normaliza el año a un valor entre 0 (más antiguo) y 1 (más reciente)
    - Interpola colores RGB:
      * Años antiguos (2012): Azul oscuro (#143264)
      * Años recientes (2025): Amarillo claro (#f0ff96)
    """
    # Evitar división por cero si todos los años son iguales
    if año_max == año_min:
        gradiente = 0.5
    else:
        # Normalizar año al rango 0-1
        gradiente = (año - año_min) / (año_max - año_min)
        gradiente = max(0, min(1, gradiente))  # Limitar entre 0 y 1

    # Interpolar valores RGB (de oscuro a claro)
    r = int(20 + (255 - 20) * gradiente)  # Rojo: 20 -> 255
    g = int(50 + (255 - 50) * gradiente)  # Verde: 50 -> 255
    b = int(100 + (150 - 100) * gradiente * 0.5)  # Azul: 100 -> 150 (más lento)

    # Convertir a formato hexadecimal
    return f'#{r:02x}{g:02x}{b:02x}'


def crear_popup_html(idx, estado_texto, estado_color, año, lat, lon):
    """
    Crea el HTML para el popup que aparece al hacer click en una reja.

    Parámetros:
    -----------
    idx : int
        Índice de la reja
    estado_texto : str
        "ABIERTA" o "CERRADA"
    estado_color : str
        Color hex para el estado
    año : int
        Año de cierre
    lat, lon : float
        Coordenadas de la reja

    Retorna:
    --------
    str
        HTML formateado para el popup
    """
    return f"""
    <div style="font-family: Arial; width: 220px;">
        <h4 style="color: #2c3e50; margin-bottom: 10px;">Reja #{idx + 1}</h4>
        <table style="width: 100%; font-size: 12px;">
            <tr>
                <td><b>Estado:</b></td>
                <td style="color: {estado_color}; font-weight: bold;">{estado_texto}</td>
            </tr>
            <tr><td><b>Año cierre:</b></td><td>{año}</td></tr>
            <tr><td><b>Coordenadas:</b></td><td>{lat:.6f}, {lon:.6f}</td></tr>
        </table>
    </div>
    """


def main():
    """
    Función principal que ejecuta todo el flujo del script.
    """
    # =========================================================================
    # PASO 1: CARGAR Y PROCESAR DATOS
    # =========================================================================
    print("="*80)
    print(" "*30 + "MAPA DE REJAS")
    print(" "*20 + "Región Metropolitana, Santiago")
    print("="*80)

    print("\n[1/5] Cargando datos desde Excel...")
    # Leer archivo Excel con pandas
    df = pd.read_excel('../01_datos_originales/Rejas.xlsx')
    print(f"      [OK] {len(df)} rejas cargadas")

    # Separar las coordenadas (vienen en formato "lat, lon")
    print("\n[2/5] Procesando coordenadas...")
    df[['Latitud', 'Longitud']] = df['cord'].str.split(',', expand=True)
    df['Latitud'] = df['Latitud'].astype(float)
    df['Longitud'] = df['Longitud'].astype(float)

    # Calcular estadísticas
    abiertas = len(df[df['estado'] == 1])
    cerradas = len(df[df['estado'] == 0])
    print(f"      [OK] Rejas abiertas: {abiertas} ({abiertas/len(df)*100:.1f}%)")
    print(f"      [OK] Rejas cerradas: {cerradas} ({cerradas/len(df)*100:.1f}%)")
    print(f"      [OK] Período: {df['año'].min()} - {df['año'].max()}")

    # =========================================================================
    # PASO 2: CREAR MAPA BASE
    # =========================================================================
    print("\n[3/5] Creando mapa base...")

    # Calcular el centro del mapa (promedio de todas las coordenadas de la región)
    centro_lat = df['Latitud'].mean()
    centro_lon = df['Longitud'].mean()

    # Crear mapa con folium
    mapa = folium.Map(
        location=[centro_lat, centro_lon],  # Centro del mapa
        zoom_start=14,                       # Nivel de zoom inicial
        tiles='OpenStreetMap'                # Estilo de mapa base
    )

    # Agregar estilos de mapa alternativos
    folium.TileLayer('CartoDB positron', name='Mapa Claro').add_to(mapa)
    folium.TileLayer('CartoDB dark_matter', name='Mapa Oscuro').add_to(mapa)
    print("      [OK] Mapa base creado")

    # =========================================================================
    # PASO 3: AGREGAR MARCADORES DE REJAS
    # =========================================================================
    print("\n[4/5] Agregando rejas al mapa...")

    # Crear grupos de marcadores para poder filtrar por estado
    grupo_abiertas = folium.FeatureGroup(name=' Rejas Abiertas (1)')
    grupo_cerradas = folium.FeatureGroup(name=' Rejas Cerradas (0)')

    # Obtener rango de años para el gradiente
    año_min = df['año'].min()
    año_max = df['año'].max()

    # Iterar sobre cada reja y crear su marcador
    for idx, row in df.iterrows():
        # Extraer datos de la reja
        lat = row['Latitud']
        lon = row['Longitud']
        estado = row['estado']  # 0 o 1
        año = row['año']

        # Determinar texto y color del estado
        estado_texto = "ABIERTA" if estado == 1 else "CERRADA"
        estado_color = "#e74c3c" if estado == 1 else "#27ae60"  # Rojo o Verde

        # Calcular color del marcador según estado
        if estado == 0:
            # REJAS CERRADAS: Color con gradiente por año
            color = calcular_color_gradiente(año, año_min, año_max)
        else:
            # REJAS ABIERTAS: Color rojo fijo
            color = '#e74c3c'

        # Crear HTML del popup (ventana que aparece al hacer click)
        popup_html = crear_popup_html(idx, estado_texto, estado_color, año, lat, lon)

        # Seleccionar el grupo según el estado
        grupo = grupo_abiertas if estado == 1 else grupo_cerradas

        # Crear el marcador circular en el mapa
        folium.CircleMarker(
            location=[lat, lon],                          # Posición
            radius=7,                                     # Tamaño del círculo
            popup=folium.Popup(popup_html, max_width=250),  # Ventana emergente
            tooltip=f"Reja #{idx+1}: {estado_texto}",    # Texto al pasar el mouse
            color=color,                                  # Color del borde
            fill=True,                                    # Rellenar el círculo
            fillColor=color,                              # Color de relleno
            fillOpacity=0.9 if estado == 0 else 0.7,    # Opacidad
            weight=2,                                     # Grosor del borde
            opacity=1.0 if estado == 0 else 0.9          # Opacidad del borde
        ).add_to(grupo)

    print(f"      [OK] {len(df)} marcadores agregados")

    # Agregar los grupos al mapa
    grupo_abiertas.add_to(mapa)
    grupo_cerradas.add_to(mapa)

    # =========================================================================
    # PASO 4: AGREGAR LEYENDA Y CONTROLES
    # =========================================================================

    # Crear leyenda HTML
    leyenda_html = f"""
    <div style="position: fixed; bottom: 50px; right: 50px; width: 280px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:13px; padding: 10px; border-radius: 5px;">
        <h4 style="margin-top: 0; margin-bottom: 10px;">Rejas - RM Santiago</h4>

        <!-- Contador de rejas abiertas -->
        <div style="margin-bottom: 12px;">
            <p style="font-size: 12px; margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px;
                      background: #e74c3c; border-radius: 50%; border: 2px solid #c0392b;
                      vertical-align: middle;"></span>
                <b>Abiertas (1):</b> {abiertas} rejas ({abiertas/len(df)*100:.0f}%)
                <br><span style="margin-left: 20px; font-size: 10px; color: #666;">
                    Puntos rojos fijos
                </span>
            </p>

            <!-- Contador de rejas cerradas -->
            <p style="font-size: 12px; margin: 5px 0; margin-top: 10px;">
                <span style="display: inline-block; width: 14px; height: 14px;
                      background: #5f93a0; border-radius: 50%; border: 2px solid #5f93a0;
                      vertical-align: middle;"></span>
                <b>Cerradas (0):</b> {cerradas} rejas ({cerradas/len(df)*100:.0f}%)
                <br><span style="margin-left: 20px; font-size: 10px; color: #666;">
                    Con gradiente por año
                </span>
            </p>
        </div>

        <hr style="border: 1px solid #ddd; margin: 10px 0;">

        <!-- Barra de gradiente de colores -->
        <p style="font-size: 11px; margin: 5px 0; font-weight: bold;">
            Gradiente año de cierre (solo cerradas):
        </p>
        <div style="margin-bottom: 8px;">
            <div style="height: 20px; background: linear-gradient(to right,
                #143264, #2d5278, #46738c, #5f93a0, #78b4b4,
                #96d46e, #b4e478, #d2f482, #f0ff96);
                border: 1px solid #666; border-radius: 3px;"></div>
            <div style="display: flex; justify-content: space-between;
                        font-size: 10px; margin-top: 3px;">
                <span><b>{año_min}</b></span>
                <span style="color: #666;">← Oscuro (antiguo) | Claro (reciente) →</span>
                <span><b>{año_max}</b></span>
            </div>
        </div>
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(leyenda_html))

    # Agregar control de capas (para filtrar abiertas/cerradas)
    folium.LayerControl().add_to(mapa)

    # Agregar botón de pantalla completa
    plugins.Fullscreen().add_to(mapa)

    # =========================================================================
    # PASO 5: GUARDAR MAPA
    # =========================================================================
    print("\n[5/5] Guardando mapa HTML...")
    output_file = '../04_mapas_html/Mapa_Rejas_RegionMetropolitana.html'
    mapa.save(output_file)
    print(f"      [OK] Mapa guardado en: {output_file}")

    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================
    print("\n" + "="*80)
    print(" "*30 + "RESUMEN FINAL")
    print("="*80)
    print(f"  Total de rejas mapeadas: {len(df)}")
    print(f"  Rejas ABIERTAS: {abiertas} ({abiertas/len(df)*100:.1f}%) - ROJO")
    print(f"  Rejas CERRADAS: {cerradas} ({cerradas/len(df)*100:.1f}%) - GRADIENTE")
    print(f"  Período: {año_min} - {año_max}")
    print(f"\n  Archivo HTML: {output_file}")
    print(f"  Abre este archivo en tu navegador web para ver el mapa interactivo")
    print("="*80)
    print("\n[OK] Proceso completado exitosamente!")


# ==============================================================================
# EJECUTAR SCRIPT
# ==============================================================================
if __name__ == "__main__":
    """
    Este bloque se ejecuta cuando corres el script directamente.

    Para ejecutar:
    1. Abre una terminal/consola
    2. Navega a la carpeta 02_scripts:
       cd "ruta/a/02_scripts"
    3. Ejecuta el script:
       python mapa_rejas_SIMPLE.py
    4. Abre el archivo HTML generado en tu navegador
    """
    main()
