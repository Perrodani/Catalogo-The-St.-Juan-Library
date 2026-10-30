import os
import re
import json
import time
import requests
from pathlib import Path

# --- CONFIGURACIÓN ---
AUDIOBOOKS_DIR = Path(r"D:\Audiolibros")
COVERS_DIR = Path("./covers")
OUTPUT_JSON = Path("./catalogo.json")
EXTENSIONS = {".m4a", ".mp3", ".m4b"}

PALABRAS_PREMIOS = [
    "Premio Planeta", "Premio Nadal", "Premio Alfaguara", "Premio Pulitzer",
    "Premio Hugo", "Premio Nebula", "Premio Cervantes", "Premio Nobel",
    "Premio Fernando Lara", "Premio Biblioteca Breve", "Premio Azorín",
    "Premio Primavera", "Premio Nacional de Narrativa", "Bestseller"
]

def limpiar_nombre_archivo(nombre_archivo):
    nombre = Path(nombre_archivo).stem
    nombre = re.sub(r'\[.*?\]', '', nombre)
    nombre = re.sub(r'\(.*?\)', '', nombre)
    nombre = nombre.replace("_", " ").strip()
    return nombre

def buscar_metadatos_google(query):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "langRestrict": "es",
        "maxResults": 1,
        "printType": "books"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "items" in data and len(data["items"]) > 0:
                info = data["items"][0].get("volumeInfo", {})
                
                titulo = info.get("title", query)
                autores = info.get("authors", ["Autor desconocido"])
                autor = ", ".join(autores)
                sinopsis = info.get("description", "Sin sinopsis disponible.")
                generos = info.get("categories", ["Ficción general"])
                
                imagenes = info.get("imageLinks", {})
                portada_url = (imagenes.get("extraLarge") or 
                               imagenes.get("large") or 
                               imagenes.get("medium") or 
                               imagenes.get("thumbnail") or "")
                
                if portada_url.startswith("http://"):
                    portada_url = portada_url.replace("http://", "https://")
                
                premio_detectado = ""
                for premio in PALABRAS_PREMIOS:
                    if premio.lower() in sinopsis.lower():
                        premio_detectado = f"🏆 {premio}"
                        break
                        
                return {
                    "title": titulo,
                    "author": autor,
                    "summary": sinopsis,
                    "genres": generos,
                    "cover_url": portada_url,
                    "award": premio_detectado
                }
    except Exception as e:
        print(f"Error consultando API para '{query}': {e}")
    return None

def descargar_portada(url, destino_path):
    if not url:
        return False
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(destino_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"Error descargando portada desde {url}: {e}")
    return False

def procesar_biblioteca():
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    catalogo = []
    
    existentes = {}
    if OUTPUT_JSON.exists():
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                datos_viejos = json.load(f)
                existentes = {item["file"]: item for item in datos_viejos if "file" in item}
        except Exception:
            pass

    if not AUDIOBOOKS_DIR.exists():
        print(f"\n[AVISO] No se encuentra la carpeta: {AUDIOBOOKS_DIR.resolve()}")
        return

    archivos = [f for f in AUDIOBOOKS_DIR.iterdir() if f.suffix.lower() in EXTENSIONS]
    total = len(archivos)
    print(f"Detectados {total} audiolibros en {AUDIOBOOKS_DIR}...")

    for i, archivo in enumerate(archivos, 1):
        nombre_limpio = limpiar_nombre_archivo(archivo.name)
        nombre_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', archivo.stem).lower()
        ruta_portada_local = COVERS_DIR / f"{nombre_safe}.jpg"
        
        if archivo.name in existentes and ruta_portada_local.exists():
            catalogo.append(existentes[archivo.name])
            print(f"[{i}/{total}] Ya catalogado: {archivo.name}")
            continue

        print(f"[{i}/{total}] Consultando: {nombre_limpio}...")
        meta = buscar_metadatos_google(nombre_limpio)
        
        if meta:
            tiene_portada = False
            if meta["cover_url"]:
                tiene_portada = descargar_portada(meta["cover_url"], ruta_portada_local)
            
            item = {
                "file": archivo.name,
                "title": meta["title"],
                "author": meta["author"],
                "series": "Independiente",
                "genres": meta["genres"],
                "award": meta["award"],
                "cover": f"covers/{nombre_safe}.jpg" if tiene_portada else "",
                "summary": meta["summary"],
                "narrators": [f"Audio: {archivo.suffix.upper()}"]
            }
        else:
            item = {
                "file": archivo.name,
                "title": nombre_limpio,
                "author": "Por verificar",
                "series": "Independiente",
                "genres": ["Audiolibros"],
                "award": "",
                "cover": "",
                "summary": "Sin descripción disponible.",
                "narrators": [f"Audio: {archivo.suffix.upper()}"]
            }
            
        catalogo.append(item)
        time.sleep(0.5)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, ensure_ascii=False, indent=2)

    print(f"\n¡Proceso completado! Archivo {OUTPUT_JSON} generado con {len(catalogo)} obras.")

if __name__ == "__main__":
    procesar_biblioteca()