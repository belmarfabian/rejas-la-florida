#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera el Clasificador - V4
Muestra nodos con al menos 2 conexiones a calles residenciales
"""

import pandas as pd
import osmnx as ox
from scipy.spatial import cKDTree
import json

print("="*70)
print("GENERANDO CLASIFICADOR - CRUCES RESIDENCIALES")
print("="*70)

# 1. Cargar datos
print("\n[1/5] Cargando datos existentes...")
df = pd.read_excel('../03_datos_procesados/Base_Combinada_Snapped_v2.xlsx')
print(f"      {len(df)} puntos clasificados")

# 2. Descargar red
print("\n[2/5] Descargando red vial...")
G = ox.graph_from_place("La Florida, Santiago, Chile", network_type='all', simplify=True)
print(f"      {len(G.nodes)} nodos")

# 3. Identificar cruces residenciales (>= 2 conexiones residenciales)
print("\n[3/5] Identificando cruces residenciales...")

residenciales = {'residential', 'living_street'}
cruces = []

for node in G.nodes():
    conexiones_res = 0

    for u, v, data in G.edges(node, data=True):
        hw = data.get('highway', '')
        tipos = set(hw) if isinstance(hw, list) else {hw}
        if tipos & residenciales:
            conexiones_res += 1

    if conexiones_res >= 2:
        data = G.nodes[node]
        cruces.append({
            'lat': data['y'],
            'lon': data['x'],
            'conexiones': conexiones_res
        })

print(f"      {len(cruces)} cruces residenciales")

# 4. Determinar estado
print("\n[4/5] Determinando estados...")

tree = cKDTree(df[['lat', 'lon']].values)
umbral = 30 / 111000

puntos = []
n_con = 0
n_sin = 0

for c in cruces:
    dist, idx = tree.query([c['lat'], c['lon']])

    if dist <= umbral:
        estado = int(df.iloc[idx]['estado'])
        estado_txt = {0: 'cerrada', 1: 'abierta', 2: 'otro'}[estado]
        n_con += 1
    else:
        estado_txt = 'pending'
        n_sin += 1

    puntos.append({
        'lat': c['lat'],
        'lon': c['lon'],
        'conexiones': c['conexiones'],
        'estadoInicial': estado_txt
    })

print(f"      Con clasificacion: {n_con}")
print(f"      Pendientes: {n_sin}")

# 5. Generar HTML
print("\n[5/5] Generando HTML...")

centro_lat = sum(p['lat'] for p in puntos) / len(puntos)
centro_lon = sum(p['lon'] for p in puntos) / len(puntos)

html = f'''<!DOCTYPE html>
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
            background: rgba(30,30,30,0.95); padding: 15px;
            border-radius: 10px; color: white; z-index: 1000;
            min-width: 280px; max-height: 90vh; overflow-y: auto;
        }}
        .control-panel h2 {{ font-size: 16px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #444; }}
        .stat-row {{ display: flex; justify-content: space-between; margin: 5px 0; font-size: 13px; }}
        .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }}
        .dot-pending {{ background: #f39c12; }}
        .dot-cerrada {{ background: #e74c3c; }}
        .dot-abierta {{ background: #2ecc71; }}
        .dot-otro {{ background: #9b59b6; }}
        .progress-bar {{ background: #333; border-radius: 5px; height: 8px; margin: 10px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #2ecc71, #27ae60); transition: width 0.3s; }}
        .btn {{ display: block; width: 100%; padding: 10px; margin: 5px 0; border: none; border-radius: 5px; cursor: pointer; font-size: 13px; font-weight: bold; }}
        .btn:hover {{ transform: scale(1.02); }}
        .btn-export {{ background: #3498db; color: white; }}
        .btn-reset {{ background: #555; color: white; }}
        .btn-cerrada {{ background: #e74c3c; color: white; }}
        .btn-abierta {{ background: #2ecc71; color: white; }}
        .btn-otro {{ background: #9b59b6; color: white; }}
        .classify-popup {{ text-align: center; min-width: 200px; }}
        .classify-popup h3 {{ margin-bottom: 10px; color: #333; }}
        .classify-popup .coord {{ font-size: 11px; color: #666; margin-bottom: 10px; }}
        .instructions {{ background: rgba(52,152,219,0.2); padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 12px; border-left: 3px solid #3498db; }}
        .filters {{ margin: 15px 0; padding-top: 10px; border-top: 1px solid #444; }}
        .filter-btn {{ padding: 5px 10px; margin: 2px; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; opacity: 0.6; }}
        .filter-btn.active {{ opacity: 1; }}
        .assistant-input {{ width: 100%; padding: 8px; border: 1px solid #444; border-radius: 5px; background: #333; color: white; margin-bottom: 10px; }}
        .toast {{ position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #333; color: white; padding: 12px 25px; border-radius: 25px; z-index: 2000; display: none; }}
        .map-legend {{ position: fixed; bottom: 20px; left: 10px; background: rgba(30,30,30,0.9); padding: 10px 15px; border-radius: 8px; color: white; z-index: 1000; font-size: 12px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="control-panel">
        <h2>Clasificador de Rejas</h2>
        <div class="instructions">
            <strong>Cruces de calles residenciales</strong><br>
            Puntos <span style="color:#f39c12;">naranjas</span> = pendientes
        </div>
        <label style="font-size: 12px; color: #aaa;">Tu nombre:</label>
        <input type="text" class="assistant-input" id="assistantName" placeholder="Ej: Juan Perez">
        <div class="stats">
            <div class="stat-row"><span><span class="dot dot-pending"></span> Pendientes:</span><span id="pendingCount">0</span></div>
            <div class="stat-row"><span><span class="dot dot-cerrada"></span> Cerradas:</span><span id="cerradaCount">0</span></div>
            <div class="stat-row"><span><span class="dot dot-abierta"></span> Abiertas:</span><span id="abiertaCount">0</span></div>
            <div class="stat-row"><span><span class="dot dot-otro"></span> Otro:</span><span id="otroCount">0</span></div>
        </div>
        <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
        <div style="text-align:center;font-size:12px;color:#888" id="progressText">0%</div>
        <div class="filters">
            <div style="font-size:12px;color:#aaa;margin-bottom:5px">Mostrar:</div>
            <button class="filter-btn active" style="background:#f39c12" onclick="toggleFilter('pending')">Pendientes</button>
            <button class="filter-btn active" style="background:#e74c3c" onclick="toggleFilter('cerrada')">Cerradas</button>
            <button class="filter-btn active" style="background:#2ecc71" onclick="toggleFilter('abierta')">Abiertas</button>
            <button class="filter-btn active" style="background:#9b59b6" onclick="toggleFilter('otro')">Otro</button>
        </div>
        <button class="btn btn-export" onclick="exportData()">Exportar Cambios</button>
        <button class="btn btn-export" style="background:#9b59b6" onclick="exportAll()">Exportar TODO</button>
        <button class="btn btn-reset" onclick="resetData()">Reiniciar</button>
    </div>
    <div class="map-legend">
        <div><span class="dot dot-pending"></span> Pendiente</div>
        <div><span class="dot dot-cerrada"></span> Cerrada</div>
        <div><span class="dot dot-abierta"></span> Abierta</div>
        <div><span class="dot dot-otro"></span> Otro</div>
    </div>
    <div class="toast" id="toast"></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const DATA={json.dumps(puntos)};
        const COLORS={{pending:'#f39c12',cerrada:'#e74c3c',abierta:'#2ecc71',otro:'#9b59b6'}};
        let markers={{}},cambios={{}},filtros={{pending:true,cerrada:true,abierta:true,otro:true}};

        const map=L.map('map').setView([{centro_lat},{centro_lon}],14);
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{maxZoom:19}}).addTo(map);

        function load(){{const s=localStorage.getItem('rejas_v4');if(s)cambios=JSON.parse(s);}}
        function save(){{localStorage.setItem('rejas_v4',JSON.stringify(cambios));}}
        function getEstado(i){{return cambios[i]?cambios[i].estado:DATA[i].estadoInicial;}}

        function createMarkers(){{
            DATA.forEach((p,i)=>{{
                const e=getEstado(i),c=COLORS[e];
                const m=L.circleMarker([p.lat,p.lon],{{
                    radius:e==='pending'?8:6,fillColor:c,color:e==='pending'?'#fff':c,
                    weight:e==='pending'?2:1,opacity:1,fillOpacity:0.8
                }});
                m.on('click',()=>openPopup(i,p));
                m.addTo(map);
                markers[i]={{marker:m}};
            }});
        }}

        function openPopup(i,p){{
            const e=getEstado(i);
            const txt={{pending:'Pendiente',cerrada:'Cerrada',abierta:'Abierta',otro:'Otro'}};
            L.popup().setLatLng([p.lat,p.lon]).setContent(`
                <div class="classify-popup">
                    <h3>Cruce #${{i+1}}</h3>
                    <div class="coord">${{p.lat.toFixed(6)}}, ${{p.lon.toFixed(6)}}</div>
                    <div style="margin-bottom:10px">Estado: <strong>${{txt[e]}}</strong></div>
                    <button class="btn btn-cerrada" onclick="clasificar(${{i}},'cerrada')">CERRADA</button>
                    <button class="btn btn-abierta" onclick="clasificar(${{i}},'abierta')">ABIERTA</button>
                    <button class="btn btn-otro" onclick="clasificar(${{i}},'otro')">OTRO</button>
                </div>
            `).openOn(map);
        }}

        function clasificar(i,e){{
            const p=DATA[i],n=document.getElementById('assistantName').value||'Anonimo';
            cambios[i]={{estado:e,lat:p.lat,lon:p.lon,prev:p.estadoInicial,time:new Date().toISOString(),por:n}};
            updateMarker(i,e);save();updateStats();map.closePopup();
            showToast(e.toUpperCase());goNext(i);
        }}

        function updateMarker(i,e){{
            const c=COLORS[e];
            markers[i].marker.setStyle({{fillColor:c,color:e==='pending'?'#fff':c,radius:e==='pending'?8:6,weight:e==='pending'?2:1}});
            if(!filtros[e])markers[i].marker.setStyle({{opacity:0,fillOpacity:0}});
        }}

        function goNext(curr){{
            for(let i=curr+1;i<DATA.length;i++)if(getEstado(i)==='pending'){{map.setView([DATA[i].lat,DATA[i].lon],17);setTimeout(()=>openPopup(i,DATA[i]),300);return;}}
            for(let i=0;i<curr;i++)if(getEstado(i)==='pending'){{map.setView([DATA[i].lat,DATA[i].lon],17);setTimeout(()=>openPopup(i,DATA[i]),300);return;}}
            showToast('Todos clasificados!');
        }}

        function updateStats(){{
            let c={{pending:0,cerrada:0,abierta:0,otro:0}};
            DATA.forEach((_,i)=>c[getEstado(i)]++);
            document.getElementById('pendingCount').textContent=c.pending;
            document.getElementById('cerradaCount').textContent=c.cerrada;
            document.getElementById('abiertaCount').textContent=c.abierta;
            document.getElementById('otroCount').textContent=c.otro;
            const pct=Math.round(((DATA.length-c.pending)/DATA.length)*100);
            document.getElementById('progressFill').style.width=pct+'%';
            document.getElementById('progressText').textContent=pct+'% ('+c.pending+' pendientes)';
        }}

        function toggleFilter(e){{
            filtros[e]=!filtros[e];
            document.querySelectorAll('.filter-btn').forEach(b=>{{if(b.textContent.toLowerCase().includes(e.substring(0,4)))b.classList.toggle('active',filtros[e]);}});
            DATA.forEach((_,i)=>{{if(getEstado(i)===e)markers[i].marker.setStyle({{opacity:filtros[e]?1:0,fillOpacity:filtros[e]?0.8:0}});}});
        }}

        function exportData(){{
            const list=Object.values(cambios);if(!list.length){{showToast('Sin cambios');return;}}
            let csv='lat,lon,estado,timestamp,por\\n';
            list.forEach(c=>csv+=c.lat+','+c.lon+','+{{cerrada:0,abierta:1,otro:2}}[c.estado]+','+c.time+',"'+c.por+'"\\n');
            download(csv,'cambios_'+new Date().toISOString().split('T')[0]+'.csv');
        }}

        function exportAll(){{
            let csv='lat,lon,estado\\n';
            DATA.forEach((p,i)=>csv+=p.lat+','+p.lon+','+{{pending:-1,cerrada:0,abierta:1,otro:2}}[getEstado(i)]+'\\n');
            download(csv,'todos_'+new Date().toISOString().split('T')[0]+'.csv');
        }}

        function download(csv,name){{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{{type:'text/csv'}}));a.download=name;a.click();}}
        function resetData(){{if(confirm('Borrar cambios?')){{cambios={{}};localStorage.removeItem('rejas_v4');DATA.forEach((p,i)=>updateMarker(i,p.estadoInicial));updateStats();}}}}
        function showToast(m){{const t=document.getElementById('toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',2000);}}

        load();createMarkers();updateStats();
        const sn=localStorage.getItem('assistant_name');if(sn)document.getElementById('assistantName').value=sn;
        document.getElementById('assistantName').onchange=function(){{localStorage.setItem('assistant_name',this.value);}};
    </script>
</body>
</html>'''

with open('../04_mapas_html/Clasificador_Rejas.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\\n{'='*70}")
print(f"Total cruces: {len(puntos)}")
print(f"Con clasificacion: {n_con}")
print(f"Pendientes: {n_sin}")
print("="*70)
