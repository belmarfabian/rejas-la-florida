#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MAPA INTERACTIVO DE REJAS - LA FLORIDA
================================================================================
Genera mapa con datos combinados de Thomas, Nicolas y Calles Abiertas.
Estados: 0=Cerrada, 1=Abierta, 2=Otro tipo de cierre
================================================================================
"""

import pandas as pd
import folium
from folium import plugins


def calcular_color_gradiente(año, año_min, año_max):
    """Calcula color para rejas cerradas basado en año de cierre."""
    if año_max == año_min:
        gradiente = 0.5
    else:
        gradiente = (año - año_min) / (año_max - año_min)
        gradiente = max(0, min(1, gradiente))

    r = int(20 + (255 - 20) * gradiente)
    g = int(50 + (255 - 50) * gradiente)
    b = int(100 + (150 - 100) * gradiente * 0.5)

    return f'#{r:02x}{g:02x}{b:02x}'


def main():
    print("="*80)
    print(" "*25 + "MAPA DE REJAS - LA FLORIDA")
    print("="*80)

    # Cargar datos combinados
    print("\n[1/5] Cargando datos combinados...")
    df = pd.read_excel('../03_datos_procesados/Base_Combinada.xlsx')
    print(f"      Total: {len(df)} rejas")

    # Estadisticas por estado
    estado_0 = len(df[df['estado'] == 0])
    estado_1 = len(df[df['estado'] == 1])
    estado_2 = len(df[df['estado'] == 2])

    print(f"      Cerradas (0): {estado_0}")
    print(f"      Abiertas (1): {estado_1}")
    print(f"      Otro tipo (2): {estado_2}")

    # Estadisticas por fuente
    print("\n      Por fuente:")
    for fuente in df['fuente'].unique():
        print(f"        - {fuente}: {len(df[df['fuente']==fuente])}")

    # Crear mapa
    print("\n[2/5] Creando mapa base...")
    centro_lat = df['lat'].mean()
    centro_lon = df['lon'].mean()

    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )

    # Capas alternativas
    folium.TileLayer('CartoDB positron', name='Mapa Claro').add_to(mapa)
    folium.TileLayer('CartoDB dark_matter', name='Mapa Oscuro').add_to(mapa)

    # Crear grupos por estado
    print("\n[3/5] Creando grupos de marcadores...")
    grupo_cerradas = folium.FeatureGroup(name=f'Cerradas ({estado_0})')
    grupo_abiertas = folium.FeatureGroup(name=f'Abiertas ({estado_1})')
    grupo_otro = folium.FeatureGroup(name=f'Otro tipo ({estado_2})')

    grupos = {0: grupo_cerradas, 1: grupo_abiertas, 2: grupo_otro}

    # Colores base
    colores_estado = {
        0: None,  # Se calcula con gradiente
        1: '#27ae60',  # Verde - Abierta
        2: '#9b59b6'   # Morado - Otro tipo
    }

    nombres_estado = {
        0: 'CERRADA',
        1: 'ABIERTA',
        2: 'OTRO TIPO'
    }

    # Rango de años para gradiente
    año_min = int(df['año'].min())
    año_max = int(df['año'].max())

    print(f"\n[4/5] Agregando {len(df)} marcadores...")

    for idx, row in df.iterrows():
        lat = row['lat']
        lon = row['lon']
        estado = int(row['estado'])
        año = int(row['año']) if pd.notna(row['año']) else año_min
        fuente = row['fuente']
        direccion = row.get('direccion', '')

        estado_texto = nombres_estado.get(estado, 'DESCONOCIDO')

        # Determinar color
        if estado == 0:
            color = calcular_color_gradiente(año, año_min, año_max)
        else:
            color = colores_estado.get(estado, '#95a5a6')

        # Crear popup
        popup_html = f"""
        <div style="font-family: Arial; width: 240px;">
            <h4 style="color: #2c3e50; margin-bottom: 10px;">Reja #{idx + 1}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr>
                    <td><b>Estado:</b></td>
                    <td style="color: {color}; font-weight: bold;">{estado_texto}</td>
                </tr>
                <tr><td><b>Año:</b></td><td>{año}</td></tr>
                <tr><td><b>Fuente:</b></td><td>{fuente}</td></tr>
                <tr><td><b>Coord:</b></td><td>{lat:.6f}, {lon:.6f}</td></tr>
        """
        if direccion and str(direccion).strip():
            popup_html += f"<tr><td><b>Dir:</b></td><td>{direccion}</td></tr>"
        popup_html += "</table></div>"

        # Agregar marcador
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"#{idx+1}: {estado_texto} ({año})",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.8,
            weight=2,
            opacity=0.9
        ).add_to(grupos[estado])

    # Agregar grupos al mapa
    for grupo in grupos.values():
        grupo.add_to(mapa)

    # Leyenda
    leyenda_html = f"""
    <div style="position: fixed; bottom: 50px; right: 50px; width: 300px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:13px; padding: 12px; border-radius: 5px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin-top: 0; margin-bottom: 10px;">Rejas - La Florida</h4>
        <p style="font-size: 11px; color: #666; margin-bottom: 10px;">
            Total: {len(df)} rejas
        </p>

        <div style="margin-bottom: 12px;">
            <p style="font-size: 12px; margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px;
                      background: #27ae60; border-radius: 50%;
                      vertical-align: middle;"></span>
                <b>Abiertas (1):</b> {estado_1} ({estado_1/len(df)*100:.0f}%)
            </p>
            <p style="font-size: 12px; margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px;
                      background: #5f93a0; border-radius: 50%;
                      vertical-align: middle;"></span>
                <b>Cerradas (0):</b> {estado_0} ({estado_0/len(df)*100:.0f}%)
            </p>
            <p style="font-size: 12px; margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px;
                      background: #9b59b6; border-radius: 50%;
                      vertical-align: middle;"></span>
                <b>Otro tipo (2):</b> {estado_2} ({estado_2/len(df)*100:.0f}%)
            </p>
        </div>

        <hr style="border: 1px solid #ddd; margin: 10px 0;">

        <p style="font-size: 11px; margin: 5px 0; font-weight: bold;">
            Gradiente año (solo cerradas):
        </p>
        <div style="margin-bottom: 8px;">
            <div style="height: 18px; background: linear-gradient(to right,
                #143264, #2d5278, #46738c, #5f93a0, #78b4b4,
                #96d46e, #b4e478, #d2f482, #f0ff96);
                border: 1px solid #666; border-radius: 3px;"></div>
            <div style="display: flex; justify-content: space-between;
                        font-size: 10px; margin-top: 3px;">
                <span><b>{año_min}</b> (antiguo)</span>
                <span><b>{año_max}</b> (reciente)</span>
            </div>
        </div>

        <hr style="border: 1px solid #ddd; margin: 10px 0;">
        <p style="font-size: 10px; color: #888; margin: 0;">
            Fuentes: Thomas, Nicolas, Calles Abiertas
        </p>
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(leyenda_html))

    # Controles
    folium.LayerControl().add_to(mapa)
    plugins.Fullscreen().add_to(mapa)

    # Guardar
    print("\n[5/5] Guardando mapa...")
    output_file = '../04_mapas_html/1_Mapa_Rejas.html'
    mapa.save(output_file)
    print(f"      Guardado: {output_file}")

    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print(f"  Total rejas: {len(df)}")
    print(f"  Abiertas: {estado_1} | Cerradas: {estado_0} | Otro: {estado_2}")
    print(f"  Periodo: {año_min} - {año_max}")
    print(f"  Archivo: {output_file}")
    print("="*80)


if __name__ == "__main__":
    main()
