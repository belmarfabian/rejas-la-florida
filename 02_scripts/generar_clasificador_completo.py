#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera el Clasificador Interactivo con TODOS los puntos posibles.
Incluye los ya clasificados y los pendientes.
"""

import pandas as pd
import osmnx as ox
from scipy.spatial import cKDTree
import json

print("="*70)
print("GENERANDO CLASIFICADOR COMPLETO")
print("="*70)

# 1. Cargar datos clasificados
print("\n[1/5] Cargando datos existentes...")
df = pd.read_excel('../03_datos_procesados/Base_Combinada_Snapped_v2.xlsx')
print(f"      {len(df)} puntos clasificados")

# 2. Descargar red vial
print("\n[2/5] Descargando red vial de La Florida...")
G = ox.graph_from_place("La Florida, Santiago, Chile", network_type='all', simplify=True)
print(f"      {len(G.nodes)} nodos, {len(G.edges)} aristas")

# 3. Identificar TODAS las intersecciones residenciales
print("\n[3/5] Identificando intersecciones residenciales...")

tipos_residenciales = {'residential', 'living_street'}
nodos_residenciales = set()

for u, v, data in G.edges(data=True):
    highway = data.get('highway', '')
    tipos = set(highway) if isinstance(highway, list) else {highway}
    if tipos & tipos_residenciales:
        nodos_residenciales.add(u)
        nodos_residenciales.add(v)

# Filtrar intersecciones (grado > 1)
todas_intersecciones = []
for node in nodos_residenciales:
    if G.degree(node) > 1:
        data = G.nodes[node]
        todas_intersecciones.append({
            'lat': data['y'],
            'lon': data['x'],
            'grado': G.degree(node)
        })

print(f"      {len(todas_intersecciones)} intersecciones totales")

# 4. Determinar estado de cada intersección
print("\n[4/5] Determinando estado de cada punto...")

tree = cKDTree(df[['lat', 'lon']].values)
umbral = 30 / 111000  # 30 metros

puntos_para_clasificador = []
n_con_clasificacion = 0
n_sin_clasificacion = 0

for inter in todas_intersecciones:
    dist, idx = tree.query([inter['lat'], inter['lon']])

    if dist <= umbral:
        # Ya tiene clasificación cercana
        estado_existente = int(df.iloc[idx]['estado'])
        estado_texto = {0: 'cerrada', 1: 'abierta', 2: 'otro'}[estado_existente]
        n_con_clasificacion += 1
    else:
        # Sin clasificación
        estado_texto = 'pending'
        n_sin_clasificacion += 1

    puntos_para_clasificador.append({
        'lat': inter['lat'],
        'lon': inter['lon'],
        'grado': inter['grado'],
        'estadoInicial': estado_texto
    })

print(f"      Con clasificación: {n_con_clasificacion}")
print(f"      Sin clasificación: {n_sin_clasificacion}")

# 5. Generar HTML
print("\n[5/5] Generando HTML...")

# Calcular centro
centro_lat = sum(p['lat'] for p in puntos_para_clasificador) / len(puntos_para_clasificador)
centro_lon = sum(p['lon'] for p in puntos_para_clasificador) / len(puntos_para_clasificador)

# Generar HTML completo
html_content = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clasificador de Rejas - La Florida</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; }}
        #map {{ height: 100vh; width: 100%; }}

        .control-panel {{
            position: fixed; top: 10px; right: 10px;
            background: rgba(30, 30, 30, 0.95);
            padding: 15px; border-radius: 10px; color: white;
            z-index: 1000; min-width: 280px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            max-height: 90vh; overflow-y: auto;
        }}

        .control-panel h2 {{
            font-size: 16px; margin-bottom: 15px;
            padding-bottom: 10px; border-bottom: 1px solid #444;
        }}

        .stats {{ margin-bottom: 15px; }}

        .stat-row {{
            display: flex; justify-content: space-between;
            margin: 5px 0; font-size: 13px;
        }}

        .stat-row .dot {{
            display: inline-block; width: 10px; height: 10px;
            border-radius: 50%; margin-right: 5px;
        }}

        .dot-pending {{ background: #f39c12; }}
        .dot-cerrada {{ background: #e74c3c; }}
        .dot-abierta {{ background: #2ecc71; }}
        .dot-otro {{ background: #9b59b6; }}

        .progress-bar {{
            background: #333; border-radius: 5px;
            height: 8px; margin: 10px 0; overflow: hidden;
        }}

        .progress-fill {{
            height: 100%; background: linear-gradient(90deg, #2ecc71, #27ae60);
            transition: width 0.3s ease;
        }}

        .btn {{
            display: block; width: 100%; padding: 10px; margin: 5px 0;
            border: none; border-radius: 5px; cursor: pointer;
            font-size: 13px; font-weight: bold; transition: all 0.2s;
        }}

        .btn:hover {{ transform: scale(1.02); }}
        .btn-export {{ background: #3498db; color: white; }}
        .btn-reset {{ background: #555; color: white; }}
        .btn-cerrada {{ background: #e74c3c; color: white; }}
        .btn-abierta {{ background: #2ecc71; color: white; }}
        .btn-otro {{ background: #9b59b6; color: white; }}
        .btn-skip {{ background: #7f8c8d; color: white; }}

        .classify-popup {{ text-align: center; min-width: 200px; }}
        .classify-popup h3 {{ margin-bottom: 10px; color: #333; }}
        .classify-popup .coord {{ font-size: 11px; color: #666; margin-bottom: 10px; }}
        .classify-popup .btn {{ margin: 5px 0; }}

        .instructions {{
            background: rgba(52, 152, 219, 0.2);
            padding: 10px; border-radius: 5px; margin-bottom: 15px;
            font-size: 12px; border-left: 3px solid #3498db;
        }}

        .filters {{
            margin: 15px 0; padding-top: 10px; border-top: 1px solid #444;
        }}

        .filter-label {{ font-size: 12px; margin-bottom: 5px; color: #aaa; }}

        .filter-btn {{
            padding: 5px 10px; margin: 2px; border: none; border-radius: 3px;
            cursor: pointer; font-size: 11px; opacity: 0.6; transition: opacity 0.2s;
        }}

        .filter-btn.active {{ opacity: 1; }}

        .assistant-input {{
            width: 100%; padding: 8px; border: 1px solid #444;
            border-radius: 5px; background: #333; color: white;
            margin-bottom: 10px; font-size: 13px;
        }}

        .assistant-input::placeholder {{ color: #888; }}

        .toast {{
            position: fixed; bottom: 20px; left: 50%;
            transform: translateX(-50%); background: #333; color: white;
            padding: 12px 25px; border-radius: 25px; z-index: 2000;
            display: none; animation: fadeInOut 2s ease;
        }}

        @keyframes fadeInOut {{
            0% {{ opacity: 0; transform: translateX(-50%) translateY(20px); }}
            15% {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
            85% {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
            100% {{ opacity: 0; transform: translateX(-50%) translateY(-20px); }}
        }}

        .map-legend {{
            position: fixed; bottom: 20px; left: 10px;
            background: rgba(30, 30, 30, 0.9);
            padding: 10px 15px; border-radius: 8px; color: white;
            z-index: 1000; font-size: 12px;
        }}

        .legend-item {{ margin: 3px 0; }}
    </style>
</head>
<body>
    <div id="map"></div>

    <div class="control-panel">
        <h2>Clasificador de Rejas</h2>

        <div class="instructions">
            Haz clic en los puntos para clasificarlos.<br>
            <span style="color:#f39c12;">Naranjas</span> = pendientes<br>
            Los demas ya tienen clasificacion previa.
        </div>

        <label style="font-size: 12px; color: #aaa;">Tu nombre:</label>
        <input type="text" class="assistant-input" id="assistantName" placeholder="Ej: Juan Perez">

        <div class="stats">
            <div class="stat-row">
                <span><span class="dot dot-pending"></span> Pendientes:</span>
                <span id="pendingCount">0</span>
            </div>
            <div class="stat-row">
                <span><span class="dot dot-cerrada"></span> Cerradas:</span>
                <span id="cerradaCount">0</span>
            </div>
            <div class="stat-row">
                <span><span class="dot dot-abierta"></span> Abiertas:</span>
                <span id="abiertaCount">0</span>
            </div>
            <div class="stat-row">
                <span><span class="dot dot-otro"></span> Otro:</span>
                <span id="otroCount">0</span>
            </div>
        </div>

        <div class="progress-bar">
            <div class="progress-fill" id="progressFill" style="width: 0%"></div>
        </div>
        <div style="text-align: center; font-size: 12px; color: #888;" id="progressText">0% completado</div>

        <div class="filters">
            <div class="filter-label">Mostrar:</div>
            <button class="filter-btn active" style="background: #f39c12;" onclick="toggleFilter('pending')">Pendientes</button>
            <button class="filter-btn active" style="background: #e74c3c;" onclick="toggleFilter('cerrada')">Cerradas</button>
            <button class="filter-btn active" style="background: #2ecc71;" onclick="toggleFilter('abierta')">Abiertas</button>
            <button class="filter-btn active" style="background: #9b59b6;" onclick="toggleFilter('otro')">Otro</button>
        </div>

        <button class="btn btn-export" onclick="exportData()">
            Exportar Clasificaciones
        </button>

        <button class="btn btn-export" style="background: #9b59b6;" onclick="exportAll()">
            Exportar TODO (incluye previos)
        </button>

        <button class="btn btn-reset" onclick="resetData()">
            Reiniciar Cambios
        </button>
    </div>

    <div class="map-legend">
        <div class="legend-item"><span class="dot dot-pending"></span> Pendiente de clasificar</div>
        <div class="legend-item"><span class="dot dot-cerrada"></span> Cerrada (con reja)</div>
        <div class="legend-item"><span class="dot dot-abierta"></span> Abierta (sin reja)</div>
        <div class="legend-item"><span class="dot dot-otro"></span> Otro tipo</div>
    </div>

    <div class="toast" id="toast"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <script>
        // DATOS - Todos los puntos posibles
        const INTERSECCIONES = {json.dumps(puntos_para_clasificador)};

        const CONFIG = {{
            centro: [{centro_lat:.6f}, {centro_lon:.6f}],
            zoom: 14,
            colores: {{
                pending: '#f39c12',
                cerrada: '#e74c3c',
                abierta: '#2ecc71',
                otro: '#9b59b6'
            }}
        }};

        let markers = {{}};
        let cambios = {{}};  // Solo guarda los cambios hechos por el usuario
        let filtros = {{ pending: true, cerrada: true, abierta: true, otro: true }};

        function loadSavedData() {{
            const saved = localStorage.getItem('clasificaciones_rejas_v2');
            if (saved) cambios = JSON.parse(saved);
        }}

        function saveData() {{
            localStorage.setItem('clasificaciones_rejas_v2', JSON.stringify(cambios));
        }}

        const map = L.map('map').setView(CONFIG.centro, CONFIG.zoom);

        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '© OpenStreetMap © CARTO',
            maxZoom: 19
        }}).addTo(map);

        function getEstado(index) {{
            if (cambios[index]) return cambios[index].estado;
            return INTERSECCIONES[index].estadoInicial;
        }}

        function createMarkers() {{
            INTERSECCIONES.forEach((inter, index) => {{
                const estado = getEstado(index);
                const color = CONFIG.colores[estado];

                const marker = L.circleMarker([inter.lat, inter.lon], {{
                    radius: estado === 'pending' ? 8 : 6,
                    fillColor: color,
                    color: estado === 'pending' ? '#fff' : color,
                    weight: estado === 'pending' ? 2 : 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }});

                marker.on('click', () => openClassifyPopup(index, inter));
                marker.addTo(map);

                markers[index] = {{ marker: marker, data: inter }};
            }});
        }}

        function openClassifyPopup(index, inter) {{
            const currentEstado = getEstado(index);
            const estadoText = {{
                'pending': 'Pendiente',
                'cerrada': 'Cerrada',
                'abierta': 'Abierta',
                'otro': 'Otro'
            }};

            const content = `
                <div class="classify-popup">
                    <h3>Punto #${{index + 1}}</h3>
                    <div class="coord">${{inter.lat.toFixed(6)}}, ${{inter.lon.toFixed(6)}}</div>
                    <div style="margin-bottom: 10px; font-size: 12px;">
                        Estado: <strong>${{estadoText[currentEstado]}}</strong>
                    </div>
                    <button class="btn btn-cerrada" onclick="clasificar(${{index}}, 'cerrada')">
                        CERRADA (con reja)
                    </button>
                    <button class="btn btn-abierta" onclick="clasificar(${{index}}, 'abierta')">
                        ABIERTA (sin reja)
                    </button>
                    <button class="btn btn-otro" onclick="clasificar(${{index}}, 'otro')">
                        OTRO TIPO
                    </button>
                </div>
            `;

            L.popup()
                .setLatLng([inter.lat, inter.lon])
                .setContent(content)
                .openOn(map);
        }}

        function clasificar(index, estado) {{
            const inter = INTERSECCIONES[index];
            const assistantName = document.getElementById('assistantName').value || 'Anonimo';

            cambios[index] = {{
                estado: estado,
                lat: inter.lat,
                lon: inter.lon,
                grado: inter.grado,
                estadoPrevio: inter.estadoInicial,
                timestamp: new Date().toISOString(),
                clasificadoPor: assistantName
            }};

            updateMarker(index, estado);
            saveData();
            updateStats();
            map.closePopup();

            const msgs = {{
                'cerrada': 'Marcada como CERRADA',
                'abierta': 'Marcada como ABIERTA',
                'otro': 'Marcada como OTRO'
            }};
            showToast(msgs[estado]);

            goToNextPending(index);
        }}

        function updateMarker(index, estado) {{
            const color = CONFIG.colores[estado];
            const marker = markers[index].marker;

            marker.setStyle({{
                fillColor: color,
                color: estado === 'pending' ? '#fff' : color,
                radius: estado === 'pending' ? 8 : 6,
                weight: estado === 'pending' ? 2 : 1
            }});

            if (!filtros[estado]) {{
                marker.setStyle({{ opacity: 0, fillOpacity: 0 }});
            }}
        }}

        function goToNextPending(currentIndex) {{
            for (let i = currentIndex + 1; i < INTERSECCIONES.length; i++) {{
                if (getEstado(i) === 'pending') {{
                    const inter = INTERSECCIONES[i];
                    map.setView([inter.lat, inter.lon], 17);
                    setTimeout(() => openClassifyPopup(i, inter), 300);
                    return;
                }}
            }}

            for (let i = 0; i < currentIndex; i++) {{
                if (getEstado(i) === 'pending') {{
                    const inter = INTERSECCIONES[i];
                    map.setView([inter.lat, inter.lon], 17);
                    setTimeout(() => openClassifyPopup(i, inter), 300);
                    return;
                }}
            }}

            showToast('Todos los puntos han sido clasificados!');
        }}

        function updateStats() {{
            let counts = {{ pending: 0, cerrada: 0, abierta: 0, otro: 0 }};

            INTERSECCIONES.forEach((_, index) => {{
                const estado = getEstado(index);
                counts[estado]++;
            }});

            document.getElementById('pendingCount').textContent = counts.pending;
            document.getElementById('cerradaCount').textContent = counts.cerrada;
            document.getElementById('abiertaCount').textContent = counts.abierta;
            document.getElementById('otroCount').textContent = counts.otro;

            const total = INTERSECCIONES.length;
            const classified = total - counts.pending;
            const percent = total > 0 ? Math.round((classified / total) * 100) : 0;

            document.getElementById('progressFill').style.width = percent + '%';
            document.getElementById('progressText').textContent = `${{percent}}% completado (${{classified}}/${{total}})`;
        }}

        function toggleFilter(estado) {{
            filtros[estado] = !filtros[estado];

            document.querySelectorAll('.filter-btn').forEach(btn => {{
                if (btn.textContent.toLowerCase().includes(estado.substring(0, 4))) {{
                    btn.classList.toggle('active', filtros[estado]);
                }}
            }});

            INTERSECCIONES.forEach((_, index) => {{
                const markerEstado = getEstado(index);
                if (markerEstado === estado) {{
                    markers[index].marker.setStyle({{
                        opacity: filtros[estado] ? 1 : 0,
                        fillOpacity: filtros[estado] ? 0.8 : 0
                    }});
                }}
            }});
        }}

        function exportData() {{
            const cambiosList = Object.values(cambios);
            if (cambiosList.length === 0) {{
                showToast('No hay cambios para exportar');
                return;
            }}

            let csv = 'lat,lon,estado,grado,estado_previo,timestamp,clasificado_por\\n';
            cambiosList.forEach(c => {{
                const estadoNum = {{ 'cerrada': 0, 'abierta': 1, 'otro': 2 }}[c.estado];
                csv += `${{c.lat}},${{c.lon}},${{estadoNum}},${{c.grado}},${{c.estadoPrevio}},${{c.timestamp}},"${{c.clasificadoPor}}"\\n`;
            }});

            downloadCSV(csv, `cambios_rejas_${{new Date().toISOString().split('T')[0]}}.csv`);
            showToast(`Exportados ${{cambiosList.length}} cambios`);
        }}

        function exportAll() {{
            let csv = 'lat,lon,estado,grado,origen\\n';

            INTERSECCIONES.forEach((inter, index) => {{
                const estado = getEstado(index);
                const estadoNum = {{ 'pending': -1, 'cerrada': 0, 'abierta': 1, 'otro': 2 }}[estado];
                const origen = cambios[index] ? 'nuevo' : 'previo';
                csv += `${{inter.lat}},${{inter.lon}},${{estadoNum}},${{inter.grado}},${{origen}}\\n`;
            }});

            downloadCSV(csv, `todos_puntos_${{new Date().toISOString().split('T')[0]}}.csv`);
            showToast(`Exportados ${{INTERSECCIONES.length}} puntos`);
        }}

        function downloadCSV(csv, filename) {{
            const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.click();
        }}

        function resetData() {{
            if (confirm('Seguro que quieres borrar todos los cambios?')) {{
                cambios = {{}};
                localStorage.removeItem('clasificaciones_rejas_v2');

                INTERSECCIONES.forEach((inter, index) => {{
                    updateMarker(index, inter.estadoInicial);
                }});

                updateStats();
                showToast('Cambios reiniciados');
            }}
        }}

        function showToast(message) {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.display = 'block';
            setTimeout(() => {{ toast.style.display = 'none'; }}, 2000);
        }}

        // Inicializar
        loadSavedData();
        createMarkers();
        updateStats();

        const savedName = localStorage.getItem('assistant_name');
        if (savedName) document.getElementById('assistantName').value = savedName;

        document.getElementById('assistantName').addEventListener('change', function() {{
            localStorage.setItem('assistant_name', this.value);
        }});
    </script>
</body>
</html>
'''

# Guardar
output_path = '../04_mapas_html/Clasificador_Rejas.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n{'='*70}")
print("CLASIFICADOR COMPLETO GENERADO")
print("="*70)
print(f"  Archivo: {output_path}")
print(f"  Total puntos: {len(puntos_para_clasificador)}")
print(f"  - Ya clasificados: {n_con_clasificacion}")
print(f"  - Pendientes: {n_sin_clasificacion}")
print("="*70)
