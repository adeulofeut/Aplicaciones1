"""Construcción de las figuras de Plotly (una función por gráfico).

Cada función recibe la tabla ya agregada por src/datos.py y devuelve una
figura con título, ejes y leyenda en español.
"""

import plotly.express as px
import plotly.graph_objects as go

# Paleta común (la misma de las actividades anteriores).
COLOR_PRIMARIO = "#1F4E79"
COLOR_SECUNDARIO = "#2E86AB"
COLOR_ACENTO = "#C73E1D"
COLORES_SEXO = {"Hombre": COLOR_PRIMARIO, "Mujer": "#F18F01", "Indeterminado": "#6C757D"}
ESCALA_CONTINUA = ["#EAF2F8", "#9DC3E6", "#2E86AB", "#1F4E79"]
FUENTE = "Segoe UI, Arial, sans-serif"


def aplicar_estilo(figura, titulo):
    """Formato común: título, fuente, fondo y márgenes."""
    figura.update_layout(
        title={"text": titulo, "x": 0.02, "font": {"size": 16, "color": "#1F2A44"}},
        font={"family": FUENTE, "size": 12, "color": "#3A4256"},
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    figura.update_xaxes(gridcolor="#E5E9F0")
    figura.update_yaxes(gridcolor="#E5E9F0")
    return figura


def mapa_departamentos(tabla, seleccionado=None):
    """Mapa de burbujas: total de muertes por departamento."""
    figura = px.scatter_geo(
        tabla, lat="latitud", lon="longitud", size="muertes", color="muertes",
        hover_name="departamento", custom_data=["departamento"],
        color_continuous_scale=ESCALA_CONTINUA, size_max=45,
        labels={"muertes": "Muertes"},
    )
    figura.update_traces(marker={"line": {"width": 1, "color": "white"}})
    if seleccionado:
        fila = tabla[tabla["departamento"] == seleccionado]
        figura.add_trace(go.Scattergeo(
            lat=fila["latitud"], lon=fila["longitud"], mode="markers",
            marker={"size": 18, "color": "rgba(0,0,0,0)", "line": {"width": 3, "color": COLOR_ACENTO}},
            hoverinfo="skip", showlegend=False,
        ))
    figura.update_geos(fitbounds="locations", showcountries=True, countrycolor="#9AA5B1",
                       showland=True, landcolor="#F3F6FA", showocean=True, oceancolor="#EAF2F8")
    aplicar_estilo(figura, "Total de muertes por departamento (clic para filtrar)")
    figura.update_layout(height=480, coloraxis_colorbar={"title": "Muertes"})
    return figura


def lineas_por_mes(tabla):
    figura = px.line(tabla, x="mes", y="muertes", markers=True,
                     labels={"mes": "Mes de 2019", "muertes": "Número de muertes"})
    figura.update_traces(line={"color": COLOR_PRIMARIO, "width": 3},
                         hovertemplate="%{x}: %{y:,} muertes<extra></extra>")
    figura.update_yaxes(rangemode="tozero")
    return aplicar_estilo(figura, "Total de muertes por mes")


def barras_ciudades_violentas(tabla):
    figura = px.bar(tabla.iloc[::-1], x="homicidios", y="municipio", orientation="h",
                    text="homicidios", hover_data=["departamento"],
                    labels={"homicidios": "Homicidios con arma de fuego (X95)", "municipio": "Municipio",
                            "departamento": "Departamento"})
    figura.update_traces(marker_color=COLOR_ACENTO, textposition="outside")
    return aplicar_estilo(figura, "5 ciudades más violentas: homicidios por arma de fuego (X95)")


def circular_menor_mortalidad(tabla):
    etiquetas = tabla["municipio"].str.title() + " (" + tabla["departamento"].str.title() + ")"
    figura = px.pie(tabla, names=etiquetas, values="muertes",
                    color_discrete_sequence=px.colors.qualitative.Safe)
    figura.update_traces(textinfo="value", hovertemplate="%{label}: %{value} muertes<extra></extra>")
    aplicar_estilo(figura, "10 ciudades con menor número de muertes")
    figura.update_layout(legend={"title": "Municipio (departamento)"})
    return figura


def barras_apiladas_sexo(tabla, orden, seleccionado=None):
    figura = px.bar(tabla, x="departamento", y="muertes", color="sexo",
                    category_orders={"departamento": orden, "sexo": list(COLORES_SEXO)},
                    color_discrete_map=COLORES_SEXO,
                    labels={"departamento": "Departamento", "muertes": "Número de muertes", "sexo": "Sexo"})
    if seleccionado:
        # Atenúa los demás departamentos para resaltar el elegido.
        for traza in figura.data:
            traza.marker.opacity = [1 if d == seleccionado else 0.3 for d in traza.x]
    figura.update_layout(barmode="stack", height=480, xaxis_tickangle=-45)
    return aplicar_estilo(figura, "Muertes por sexo en cada departamento")


def histograma_edad(tabla):
    figura = px.histogram(tabla, x="categoria_edad", y="muertes",
                          category_orders={"categoria_edad": list(tabla["categoria_edad"])},
                          labels={"categoria_edad": "Grupo de edad", "muertes": "Número de muertes"})
    figura.update_traces(marker_color=COLOR_SECUNDARIO,
                         hovertemplate="%{x}: %{y:,} muertes<extra></extra>")
    figura.update_layout(yaxis_title="Número de muertes", bargap=0.08, xaxis_tickangle=-30)
    return aplicar_estilo(figura, "Distribución de muertes por grupo de edad")
