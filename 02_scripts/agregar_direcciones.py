"""
Script para agregar direcciones a las rejas usando geocodificación inversa
(Reverse Geocoding)

Toma las coordenadas lat/lon del archivo Rejas.xlsx y obtiene las direcciones
de las calles usando OpenStreetMap.
"""

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import os

def obtener_direccion(lat, lon, geolocator, reintentos=3):
    """
    Hace geocodificación inversa: convierte coordenadas en dirección.

    Args:
        lat: Latitud
        lon: Longitud
        geolocator: Objeto de geopy para hacer la consulta
        reintentos: Número de intentos si falla

    Returns:
        Dirección como string, o None si falla
    """
    for intento in range(reintentos):
        try:
            # Geocodificación inversa
            location = geolocator.reverse(f"{lat}, {lon}", language='es', timeout=10)

            if location and location.address:
                # Extraer solo la calle y número si está disponible
                address = location.raw.get('address', {})

                # Intentar construir dirección legible
                partes = []

                # Nombre de calle
                if 'road' in address:
                    partes.append(address['road'])
                elif 'street' in address:
                    partes.append(address['street'])

                # Número
                if 'house_number' in address:
                    partes.append(address['house_number'])

                # Comuna
                if 'municipality' in address:
                    partes.append(address['municipality'])
                elif 'suburb' in address:
                    partes.append(address['suburb'])
                elif 'city' in address:
                    partes.append(address['city'])

                if partes:
                    return ', '.join(partes)
                else:
                    # Si no hay partes específicas, devolver dirección completa
                    return location.address

            return None

        except GeocoderTimedOut:
            print(f"  Timeout en intento {intento + 1}/{reintentos}")
            if intento < reintentos - 1:
                time.sleep(2)
        except GeocoderServiceError as e:
            print(f"  Error del servicio: {e}")
            return None
        except Exception as e:
            print(f"  Error inesperado: {e}")
            return None

    return None

def main():
    print("="*70)
    print("GEOCODIFICACION INVERSA - Obtener direcciones desde coordenadas")
    print("="*70)

    # 1. CARGAR DATOS
    print("\n[Paso 1/4] Cargando datos de Rejas.xlsx...")
    ruta_excel = '../01_datos_originales/Rejas.xlsx'

    if not os.path.exists(ruta_excel):
        ruta_excel = '01_datos_originales/Rejas.xlsx'

    df = pd.read_excel(ruta_excel)
    print(f"[OK] {len(df)} rejas cargadas")

    # 2. PARSEAR COORDENADAS
    print("\n[Paso 2/4] Parseando coordenadas...")
    df[['lat', 'lon']] = df['cord'].str.split(',', expand=True)
    df['lat'] = df['lat'].astype(float)
    df['lon'] = df['lon'].astype(float)
    print("[OK] Coordenadas parseadas")

    # 3. INICIALIZAR GEOLOCATOR
    print("\n[Paso 3/4] Inicializando geocodificador...")
    geolocator = Nominatim(user_agent="mapa_rejas_chile")
    print("[OK] Geocodificador listo")

    # 4. OBTENER DIRECCIONES
    print("\n[Paso 4/4] Obteniendo direcciones (esto puede tomar varios minutos)...")
    print("NOTA: Se hace una pausa de 1.5s entre consultas para respetar límites de API")

    direcciones = []
    total = len(df)
    exitosas = 0

    for idx, row in df.iterrows():
        print(f"\nProcesando {idx+1}/{total}: ({row['lat']}, {row['lon']})")

        direccion = obtener_direccion(row['lat'], row['lon'], geolocator)

        if direccion:
            print(f"  [OK] {direccion}")
            exitosas += 1
        else:
            direccion = "No disponible"
            print(f"  [X] No se pudo obtener dirección")

        direcciones.append(direccion)

        # Pausa para respetar límites de la API
        if idx < total - 1:  # No esperar en la última
            time.sleep(1.5)

    # 5. AGREGAR COLUMNA Y GUARDAR
    print("\n" + "="*70)
    print(f"Geocodificación completada: {exitosas}/{total} direcciones obtenidas ({exitosas/total*100:.1f}%)")

    df['direccion'] = direcciones

    # Guardar nuevo archivo
    ruta_salida = '../01_datos_originales/Rejas_con_direcciones.xlsx'
    if not os.path.exists('../01_datos_originales'):
        ruta_salida = '01_datos_originales/Rejas_con_direcciones.xlsx'

    df.to_excel(ruta_salida, index=False)
    print(f"\n[OK] Archivo guardado: {ruta_salida}")

    # Mostrar muestra
    print("\nMuestra de datos:")
    print(df[['cord', 'direccion', 'estado', 'año']].head(10).to_string())

    print("\n" + "="*70)
    print("PROCESO COMPLETADO")
    print("="*70)

if __name__ == "__main__":
    main()
