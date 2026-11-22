"""
PARTE 2 - Dashboard interactivo con Streamlit.

Ejecución:  streamlit run app.py
(antes hay que haber ejecutado scraper.py para generar los CSV)
"""
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard Books to Scrape", page_icon="📚", layout="wide")


# ---------------------------------------------------------------- 1. CARGA DE DATOS
@st.cache_data  # evita releer los CSV en cada interacción del usuario
def cargar_datos():
    libros = pd.read_csv("libros.csv")
    precios = pd.read_csv("precios.csv")
    # Unimos los dos CSV por la clave común "id".
    return libros.merge(precios, on="id")


df = cargar_datos()

st.title("📚 Dashboard de libros - Books to Scrape")
st.caption("Datos obtenidos con BeautifulSoup desde books.toscrape.com (web creada para practicar scraping).")

# ---------------------------------------------------------------- 2. FILTROS (barra lateral)
st.sidebar.header("Filtros")

categorias = st.sidebar.multiselect(
    "Categoría", sorted(df["categoria"].unique()), placeholder="Todas las categorías"
)
ratings = st.sidebar.multiselect("Rating (estrellas)", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])
precio_min, precio_max = float(df["precio"].min()), float(df["precio"].max())
rango_precio = st.sidebar.slider("Rango de precio (£)", precio_min, precio_max, (precio_min, precio_max))
solo_disponibles = st.sidebar.checkbox("Solo libros disponibles")
busqueda = st.sidebar.text_input("Buscar en el título")

# Aplicamos los filtros sobre una copia del DataFrame.
filtrado = df[df["rating"].isin(ratings) & df["precio"].between(*rango_precio)]
if categorias:  # si no se elige ninguna, se muestran todas
    filtrado = filtrado[filtrado["categoria"].isin(categorias)]
if solo_disponibles:
    filtrado = filtrado[filtrado["disponible"]]
if busqueda:
    filtrado = filtrado[filtrado["titulo"].str.contains(busqueda, case=False, regex=False)]

# Si los filtros no devuelven nada, avisamos y paramos para no romper los gráficos.
if filtrado.empty:
    st.warning("Ningún libro cumple los filtros seleccionados. Prueba a ampliarlos.")
    st.stop()

# ---------------------------------------------------------------- 3. MÉTRICAS Y TABLA
c1, c2, c3 = st.columns(3)
c1.metric("Libros encontrados", len(filtrado))
c2.metric("Precio medio", f"£{filtrado['precio'].mean():.2f}")
c3.metric("Rating medio", f"{filtrado['rating'].mean():.2f} ⭐")

st.subheader("Tabla de resultados")
st.dataframe(
    filtrado[["titulo", "categoria", "rating", "precio", "disponible", "url_libro"]],
    width='stretch',
    hide_index=True,
    column_config={
        "precio": st.column_config.NumberColumn("Precio (£)", format="£%.2f"),
        "url_libro": st.column_config.LinkColumn("Enlace", display_text="Ver libro"),
    },
)

# ---------------------------------------------------------------- 4. GRÁFICOS
st.subheader("Gráficos")
g1, g2 = st.columns(2)

# Gráfico 1: distribución de precios (barras).
fig_precios = px.histogram(
    filtrado, x="precio", nbins=20, title="Distribución de precios",
    labels={"precio": "Precio (£)", "count": "Nº de libros"},
)
fig_precios.update_layout(yaxis_title="Nº de libros")
g1.plotly_chart(fig_precios, width='stretch')

# Gráfico 2: número de libros por rating (barras).
por_rating = filtrado["rating"].value_counts().sort_index().reset_index()
por_rating.columns = ["rating", "libros"]
fig_rating = px.bar(
    por_rating, x="rating", y="libros", title="Libros por puntuación (estrellas)",
    labels={"rating": "Rating", "libros": "Nº de libros"},
)
g2.plotly_chart(fig_rating, width='stretch')

# Gráfico 3: precio medio por categoría (top 15 más caras).
precio_cat = (
    filtrado.groupby("categoria")["precio"].mean().sort_values(ascending=False).head(15).reset_index()
)
fig_cat = px.bar(
    precio_cat, x="precio", y="categoria", orientation="h",
    title="Precio medio por categoría (top 15)",
    labels={"precio": "Precio medio (£)", "categoria": "Categoría"},
)
fig_cat.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_cat, width='stretch')

# ---------------------------------------------------------------- 5. ANÁLISIS CRÍTICO
# Pregunta de análisis: ¿influye el precio en la valoración de un libro?
st.subheader("¿Influye el precio en la valoración?")
fig_box = px.box(
    filtrado, x="rating", y="precio", points="all",
    title="Precio según rating",
    labels={"rating": "Rating (estrellas)", "precio": "Precio (£)"},
)
st.plotly_chart(fig_box, width='stretch')

# Calculamos la correlación de Pearson (-1 a 1) y la interpretamos automáticamente.
if filtrado["rating"].nunique() > 1 and filtrado["precio"].nunique() > 1:
    corr = filtrado["precio"].corr(filtrado["rating"])
    if abs(corr) < 0.1:
        lectura = "prácticamente **no hay relación**: un libro más caro no está mejor valorado."
    elif abs(corr) < 0.4:
        lectura = f"existe una relación **débil {'positiva' if corr > 0 else 'negativa'}**."
    else:
        lectura = f"existe una relación **{'positiva' if corr > 0 else 'negativa'}** clara."
    st.info(f"Correlación precio-rating: **{corr:.2f}** → {lectura}")
else:
    st.info("Con los filtros actuales no hay variedad suficiente para calcular la correlación.")
