import os
import json
import re
import requests
from pathlib import Path

# --- CONFIGURACIÓN ---
ABS_URL = "http://192.168.178.188:13378"
ABS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlJZCI6IjZiMmJiNzMzLWVlMGQtNGIxNy1hMzMyLTA1ZjQ1MzIxZjdhMSIsIm5hbWUiOiJDYXRhbG9nbyBUaGUgU3QuIEp1YW4gTGlicmFyeSIsInR5cGUiOiJhcGkiLCJpYXQiOjE3OTMzOTkyMDN9.NMX44EmWkaSdMWQc43AbvuEMrh2K4o1MpOoUKBkTkeU"

COVERS_DIR = Path("./covers")
OUTPUT_JSON = Path("./catalogo.json")
OUTPUT_JS = Path("./catalogo_datos.js")

HEADERS = {
    "Authorization": f"Bearer {ABS_TOKEN}"
}

PALABRAS_PREMIOS = [
    "Premio Planeta", "Premio Nadal", "Premio Alfaguara", "Premio Pulitzer",
    "Premio Hugo", "Premio Nebula", "Premio Cervantes", "Premio Nobel",
    "Premio Fernando Lara", "Premio Biblioteca Breve", "Premio Azorín",
    "Premio Primavera", "Premio Nacional de Narrativa", "Bestseller"
]

def obtener_bibliotecas():
    url = f"{ABS_URL}/api/libraries"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("libraries", [])
        else:
            print(f"[ERROR] Código {r.status_code} al conectar. Revisa el Token de Audiobookshelf.")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar con el servidor en {ABS_URL}: {e}")
    return []

def descargar_portada_abs(item_id, destino_path):
    url = f"{ABS_URL}/api/items/{item_id}/cover"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            with open(destino_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

def procesar():
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    bibliotecas = obtener_bibliotecas()
    
    if not bibliotecas:
        print("No se pudieron cargar las bibliotecas de Audiobookshelf.")
        return

    catalogo = []
    
    for lib in bibliotecas:
        lib_id = lib.get("id")
        lib_name = lib.get("name")
        print(f"Leyendo biblioteca: {lib_name}...")
        
        url_items = f"{ABS_URL}/api/libraries/{lib_id}/items?limit=0"
        try:
            r = requests.get(url_items, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                continue
            items = r.json().get("results", [])
        except Exception as e:
            print(f"Error al leer los audiolibros: {e}")
            continue

        total = len(items)
        print(f"Encontrados {total} audiolibros. Exportando portadas y metadatos...")

        for i, item in enumerate(items, 1):
            media = item.get("media", {})
            metadata = media.get("metadata", {})
            item_id = item.get("id")

            titulo = metadata.get("title") or "Sin título"
            autor = metadata.get("authorName") or "Autor desconocido"
            sinopsis = metadata.get("description") or "Sin sinopsis disponible."
            sinopsis_limpia = re.sub(r'<[^>]+>', '', sinopsis).strip()

            generos = metadata.get("genres", [])
            if not generos:
                generos = ["Audiolibro"]

            saga = metadata.get("seriesName") or "Independiente"
            if metadata.get("seriesSequence"):
                saga += f" · Vol. {metadata.get('seriesSequence')}"

            narradores = metadata.get("narratorName")
            lista_narradores = [narradores] if narradores else ["Audio estándar"]

            premio_detectado = ""
            for premio in PALABRAS_PREMIOS:
                if premio.lower() in sinopsis_limpia.lower():
                    premio_detectado = f"🏆 {premio}"
                    break

            nombre_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', f"{titulo}_{autor}").lower()[:50]
            ruta_portada = COVERS_DIR / f"{nombre_safe}.jpg"
            
            tiene_portada = False
            if not ruta_portada.exists():
                tiene_portada = descargar_portada_abs(item_id, ruta_portada)
            else:
                tiene_portada = True

            catalogo.append({
                "title": titulo,
                "author": autor,
                "series": saga,
                "genres": generos,
                "award": premio_detectado,
                "cover": f"covers/{nombre_safe}.jpg" if tiene_portada else "",
                "summary": sinopsis_limpia,
                "narrators": lista_narradores
            })

            if i % 100 == 0 or i == total:
                print(f"Progreso: {i}/{total} procesados...")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("const DATOS_AUDIOLIBROS = " + json.dumps(catalogo, ensure_ascii=False) + ";")

    print(f"\n¡Completado con éxito! Generado catalogo_datos.js con {len(catalogo)} obras directas de Audiobookshelf.")

if __name__ == "__main__":
    procesar()