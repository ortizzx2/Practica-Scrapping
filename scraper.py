"""
PARTE 1 - Web scraping de https://books.toscrape.com con BeautifulSoup.

Genera dos CSV:
  - libros.csv  -> datos descriptivos (titulo, categoria, rating, enlaces)
  - precios.csv -> datos económicos (precio, disponibilidad, fecha de extracción)
Ambos se relacionan por la columna "id".

Ejecución:  python scraper.py
"""
import time
from datetime import date
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------- CONFIGURACIÓN
BASE_URL = "http://books.toscrape.com/"
# Nos identificamos con un User-Agent claro (buena práctica ética).
HEADERS = {"User-Agent": "PracticaScraping-Estudiante/1.0 (proyecto educativo)"}
# Pausa entre peticiones para no saturar el servidor (rate limiting).
RETARDO = 1  # segundos

# El rating viene escrito en una clase CSS ("star-rating Three"); lo pasamos a número.
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


# ---------------------------------------------------------------- UTILIDADES
def comprobar_robots():
    """Lee robots.txt y avisa si el scraping está permitido."""
    rp = RobotFileParser(urljoin(BASE_URL, "robots.txt"))
    rp.read()
    # Si robots.txt no existe (404), la librería considera que todo está permitido.
    permitido = rp.can_fetch(HEADERS["User-Agent"], BASE_URL)
    print(f"robots.txt -> scraping permitido: {permitido}")
    return permitido


def obtener_soup(url):
    """Descarga una URL (con pausa) y devuelve su HTML analizado con BeautifulSoup."""
    time.sleep(RETARDO)
    respuesta = requests.get(url, headers=HEADERS, timeout=15)
    respuesta.raise_for_status()
    # La web no declara bien la codificación y "£" se rompe ("Â£"); forzamos UTF-8.
    respuesta.encoding = "utf-8"
    return BeautifulSoup(respuesta.text, "html.parser")


def obtener_categorias():
    """Devuelve {nombre_categoria: url} leyendo el menú lateral de la portada."""
    soup = obtener_soup(BASE_URL)
    enlaces = soup.select("div.side_categories ul li ul li a")  # ignora "Books" (todas)
    return {a.get_text(strip=True): urljoin(BASE_URL, a["href"]) for a in enlaces}


def parsear_libro(articulo, categoria, url_pagina):
    """Extrae y LIMPIA los datos de un libro (una etiqueta <article class='product_pod'>)."""
    enlace = articulo.h3.a
    # El título completo está en el atributo title (el texto visible aparece cortado con "...").
    titulo = enlace["title"]
    url_libro = urljoin(url_pagina, enlace["href"])
    url_portada = urljoin(url_pagina, articulo.img["src"])

    # Limpieza: "£51.77" -> 51.77 (float)
    precio = float(articulo.select_one("p.price_color").get_text(strip=True).replace("£", ""))

    # Limpieza: clase "star-rating Three" -> 3 (int)
    clase_rating = articulo.select_one("p.star-rating")["class"][1]
    rating = RATINGS[clase_rating]

    # Limpieza: "In stock" -> True/False
    disponible = "in stock" in articulo.select_one("p.availability").get_text(strip=True).lower()

    return {
        "titulo": titulo,
        "categoria": categoria,
        "rating": rating,
        "url_libro": url_libro,
        "url_portada": url_portada,
        "precio": precio,
        "disponible": disponible,
    }


def scrapear_categoria(nombre, url):
    """Recorre todas las páginas (paginación) de una categoría."""
    libros = []
    while url:
        soup = obtener_soup(url)
        for articulo in soup.select("article.product_pod"):
            libros.append(parsear_libro(articulo, nombre, url))
        # Si existe el botón "next" seguimos a la siguiente página; si no, terminamos.
        siguiente = soup.select_one("li.next a")
        url = urljoin(url, siguiente["href"]) if siguiente else None
    return libros


# ---------------------------------------------------------------- PROGRAMA PRINCIPAL
def main():
    if not comprobar_robots():
        print("El sitio no permite scraping. Abortando.")
        return

    categorias = obtener_categorias()
    print(f"{len(categorias)} categorías encontradas")

    todos = []
    for i, (nombre, url) in enumerate(categorias.items(), start=1):
        libros = scrapear_categoria(nombre, url)
        todos.extend(libros)
        print(f"[{i}/{len(categorias)}] {nombre}: {len(libros)} libros")

    df = pd.DataFrame(todos)
    # Cada libro pertenece a una sola categoría, así que eliminamos posibles duplicados.
    df = df.drop_duplicates(subset="url_libro").reset_index(drop=True)
    df.insert(0, "id", df.index + 1)  # identificador para relacionar ambos CSV
    df["fecha_extraccion"] = date.today().isoformat()  # columna de tipo fecha

    # Dos archivos CSV: datos del libro por un lado, datos económicos por otro.
    libros_df = df[["id", "titulo", "categoria", "rating", "url_libro", "url_portada"]]
    precios_df = df[["id", "precio", "disponible", "fecha_extraccion"]]
    libros_df.to_csv("libros.csv", index=False, encoding="utf-8")
    precios_df.to_csv("precios.csv", index=False, encoding="utf-8")
    print(f"Guardados libros.csv y precios.csv ({len(df)} libros)")


if __name__ == "__main__":
    main()
