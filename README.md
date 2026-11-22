# Práctica de Web Scraping con BeautifulSoup y Streamlit

Scraping de [Books to Scrape](http://books.toscrape.com) (web creada para practicar scraping), tratamiento con Pandas y dashboard interactivo con Streamlit.

## Archivos

| Archivo | Función |
|---|---|
| `scraper.py` | Parte 1: extrae los 1000 libros y genera los CSV |
| `libros.csv` | id, título, categoría, rating, enlace del libro, enlace de la portada |
| `precios.csv` | id, precio, disponibilidad, fecha de extracción |
| `app.py` | Parte 2: dashboard con Streamlit |
| `requirements.txt` | Dependencias |

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
python scraper.py          # opcional: los CSV ya están incluidos
streamlit run app.py
```

## Ética y buenas prácticas

- Se comprueba `robots.txt` con `urllib.robotparser` (en este sitio devuelve 404, es decir, no hay restricciones).
- Se envía un `User-Agent` que identifica el proyecto.
- Pausa de 1 segundo entre peticiones (`time.sleep`) para no saturar el servidor.
- No se recogen datos personales ni se hace login.

## Decisiones técnicas (para defender la práctica)

- **Scraping por categorías**: el listado general no indica la categoría de cada libro. Recorrer las 50 categorías (con su paginación) da la categoría sin tener que abrir las 1000 fichas, lo que reduce las peticiones de ~1000 a ~100.
- **Título desde el atributo `title`**: el texto visible del enlace está cortado con "...".
- **Rating**: viene como clase CSS (`star-rating Three`); se convierte a número (3).
- **Precio**: `"£51.77"` se limpia y se guarda como `float` dentro del script, no a mano.
- **Codificación**: se fuerza UTF-8 porque, si no, el símbolo `£` aparece como `Â£`.
- **Dos CSV** relacionados por `id`; la app los une con `merge`.
- **Fecha**: el sitio no publica fechas, por eso se añade `fecha_extraccion`.

## Análisis

La pregunta del dashboard es *¿influye el precio en la valoración?* Con boxplot y correlación de Pearson se obtiene ≈ 0,03: **no hay relación**. Es esperable porque los datos de esta web son ficticios y los precios son aleatorios.
