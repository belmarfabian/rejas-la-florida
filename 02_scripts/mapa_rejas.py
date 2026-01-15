#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapa de Rejas en La Florida
Estado: 1 = Abierto, 0 = Cerrado
Coloreado por año con gradiente continuo
"""

import pandas as pd
import folium
from folium import plugins

def main():
    print("="*80)
    print(" "*30 + "MAPA DE REJAS")
    print(" "*25 + "La Florida, Santiago")
    print("="*80)

    # Leer datos
    print("\n1. Cargando datos de Rejas.xlsx...")
    df = pd.read_excel('../datos_originales/Rejas.xlsx')
    print(f"   Total de rejas: {len(df)}")

    # Separar coordenadas
    print("\n2. Procesando coordenadas...")
    df[['Latitud', 'Longitud']] = df['cord'].str.split(',', expand=True)
    df['Latitud'] = df['Latitud'].astype(float)
    df['Longitud'] = df['Longitud'].astype(float)

    # Estadísticas
    abiertas = len(df[df['estado'] == 1])
    cerradas = len(df[df['estado'] == 0])

    print(f"   Rejas abiertas (1): {abiertas} ({abiertas/len(df)*100:.1f}%)")
    print(f"   Rejas cerradas (0): {cerradas} ({cerradas/len(df)*100:.1f}%)")
    print(f"\n   Años: {df['año'].min()} - {df['año'].max()}")

    # Crear mapa
    print("\n3. Generando mapa interactivo...")

    # Centro en La Florida
    centro_lat = df['Latitud'].mean()
    centro_lon = df['Longitud'].mean()

    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=14,
        tiles='OpenStreetMap'
    )

    # Agregar capas alternativas
    folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(mapa)
    folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(mapa)

    # Crear grupos por estado
    grupo_abiertas = folium.FeatureGroup(name='Rejas Abiertas (1)')
    grupo_cerradas = folium.FeatureGroup(name='Rejas Cerradas (0)')

    # Rango de años para gradiente
    año_min = df['año'].min()
    año_max = df['año'].max()

    print(f"\n4. Agregando {len(df)} rejas al mapa...")

    for idx, row in df.iterrows():
        lat = row['Latitud']
        lon = row['Longitud']
        estado = row['estado']
        año = row['año']

        # Estado texto
        estado_texto = "ABIERTA" if estado == 1 else "CERRADA"
        estado_color = "#2ecc71" if estado == 1 else "#e74c3c"

        # Color según estado
        if estado == 0:
            # CERRADAS: Calcular color según año (gradiente continuo)
            gradiente = (año - año_min) / (año_max - año_min) if año_max > año_min else 0.5
            gradiente = max(0, min(1, gradiente))

            # Gradiente de oscuro (antiguo) a claro (moderno)
            r = int(20 + (255 - 20) * gradiente)
            g = int(50 + (255 - 50) * gradiente)
            b = int(100 + (150 - 100) * gradiente * 0.5)
            color = f'#{r:02x}{g:02x}{b:02x}'
        else:
            # ABIERTAS: Rojo
            color = '#e74c3c'

        # Crear popup
        popup_html = f"""
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

        # Seleccionar grupo según estado
        grupo = grupo_abiertas if estado == 1 else grupo_cerradas

        # Crear marcador - mismo tamaño para todos (radio 7)
        if estado == 1:
            # Rejas abiertas: círculo rojo
            folium.CircleMarker(
                location=[lat, lon],
                radius=7,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"Reja #{idx+1}: {estado_texto}",
                color='#c0392b',
                fill=True,
                fillColor='#e74c3c',
                fillOpacity=0.7,
                weight=2,
                opacity=0.9
            ).add_to(grupo)
        else:
            # Rejas cerradas: círculo con gradiente de color por año
            folium.CircleMarker(
                location=[lat, lon],
                radius=7,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"Reja #{idx+1}: {estado_texto} ({año})",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.9,
                weight=2,
                opacity=1.0
            ).add_to(grupo)

    # Agregar grupos al mapa
    grupo_abiertas.add_to(mapa)
    grupo_cerradas.add_to(mapa)

    # Leyenda
    leyenda_html = f"""
    <div style="position: fixed;
                bottom: 50px; right: 50px; width: 280px;
                background-color: white; border:2px solid grey;
                z-index:9999; font-size:13px; padding: 10px;
                border-radius: 5px;">
        <h4 style="margin-top: 0; margin-bottom: 10px;">Rejas - La Florida</h4>

        <div style="margin-bottom: 12px;">
            <p style="font-size: 12px; margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px;
                      background: #e74c3c; border-radius: 50%; border: 2px solid #c0392b;
                      vertical-align: middle;"></span>
                <b>Abiertas (1):</b> {abiertas} rejas ({abiertas/len(df)*100:.0f}%)
                <br><span style="margin-left: 20px; font-size: 10px; color: #666;">Puntos rojos</span>
            </p>
            <p style="font-size: 12px; margin: 5px 0; margin-top: 10px;">
                <span style="display: inline-block; width: 14px; height: 14px;
                      background: #5f93a0; border-radius: 50%; border: 2px solid #5f93a0;
                      vertical-align: middle;"></span>
                <b>Cerradas (0):</b> {cerradas} rejas ({cerradas/len(df)*100:.0f}%)
                <br><span style="margin-left: 20px; font-size: 10px; color: #666;">Con gradiente por año de cierre</span>
            </p>
        </div>

        <hr style="border: 1px solid #ddd; margin: 10px 0;">

        <p style="font-size: 11px; margin: 5px 0; font-weight: bold;">
            Gradiente año de cierre (solo cerradas):
        </p>
        <div style="margin-bottom: 8px;">
            <div style="height: 20px; background: linear-gradient(to right,
                #143264, #2d5278, #46738c, #5f93a0, #78b4b4,
                #96d46e, #b4e478, #d2f482, #f0ff96);
                border: 1px solid #666; border-radius: 3px;"></div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; margin-top: 3px;">
                <span><b>{año_min}</b></span>
                <span style="color: #666;">← Oscuro (antiguo) | Claro (reciente) →</span>
                <span><b>{año_max}</b></span>
            </div>
        </div>
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(leyenda_html))

    # Control de capas
    folium.LayerControl().add_to(mapa)

    # Plugin fullscreen
    plugins.Fullscreen().add_to(mapa)

    # Guardar
    output_file = '../mapas_html/Mapa_Rejas_LaFlorida.html'
    mapa.save(output_file)

    print(f"\n   Mapa guardado: {output_file}")

    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80)
    print(f"  Total de rejas mapeadas: {len(df)}")
    print(f"  Rejas ABIERTAS: {abiertas} ({abiertas/len(df)*100:.1f}%)")
    print(f"  Rejas CERRADAS: {cerradas} ({cerradas/len(df)*100:.1f}%)")
    print(f"  Período: {año_min} - {año_max}")
    print(f"\n  Archivo generado: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
