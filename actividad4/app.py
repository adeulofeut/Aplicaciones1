"""Aplicación web: análisis de la mortalidad en Colombia, 2019 (DANE).

Ejecución local:   python app.py   -> http://127.0.0.1:8050
Producción:        gunicorn app:server
"""

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, dash_table, dcc, html, ctx

from src import datos, graficos

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY],
           title="Mortalidad en Colombia 2019")
server = app.server  # lo usa gunicorn en el despliegue

# Integrantes del grupo (se muestran en el pie de página).
AUTORES = ["Ronald Andres Garcia Diaz", "Juan Camilo Narváez Sánchez",
           "Adrián Felipe Deulofeut Gil"]


def tarjeta_indicador(identificador, titulo):
    """Tarjeta con una cifra resumen que se actualiza con los filtros."""
    return dbc.Card(dbc.CardBody([
        html.P(titulo, className="indicador-titulo"),
        html.H3(id=identificador, className="indicador-valor"),
    ]), className="h-100")


def tarjeta_grafico(identificador, ancho):
    return dbc.Col(dbc.Card(dcc.Graph(id=identificador, config={"displaylogo": False})),
                   lg=ancho, className="mb-4")


panel_filtros = dbc.Card(dbc.CardBody(dbc.Row([
    dbc.Col([
        dbc.Label("Departamento"),
        dcc.Dropdown(id="filtro-departamento",
                     options=[datos.TODOS] + datos.lista_departamentos(),
                     value=datos.TODOS, clearable=False),
    ], md=4),
    dbc.Col([
        dbc.Label("Sexo"),
        dbc.RadioItems(id="filtro-sexo", options=[datos.TODOS, "Hombre", "Mujer"],
                       value=datos.TODOS, inline=True),
    ], md=3),
    dbc.Col([
        dbc.Label("Meses"),
        dcc.RangeSlider(id="filtro-meses", min=1, max=12, step=1, value=[1, 12],
                        marks={i + 1: mes for i, mes in enumerate(datos.MESES)}),
    ], md=4),
    dbc.Col(dbc.Button("Limpiar", id="boton-limpiar", color="secondary", outline=True,
                       className="mt-4 w-100"), md=1),
])), className="mb-4 panel-filtros")

tabla_causas = dbc.Col(dbc.Card(dbc.CardBody([
    html.H5("10 principales causas de muerte", className="titulo-tabla"),
    dash_table.DataTable(
        id="tabla-causas",
        columns=[{"name": "Código CIE-10", "id": "cod_muerte"},
                 {"name": "Causa de muerte", "id": "causa"},
                 {"name": "Total de casos", "id": "total", "type": "numeric",
                  "format": {"specifier": ",d"}}],
        style_header={"backgroundColor": graficos.COLOR_PRIMARIO, "color": "white", "fontWeight": "bold"},
        style_cell={"fontFamily": graficos.FUENTE, "padding": "8px", "textAlign": "left",
                    "whiteSpace": "normal", "height": "auto"},
        style_cell_conditional=[{"if": {"column_id": "total"}, "textAlign": "right"}],
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#F3F6FA"}],
    ),
])), lg=12, className="mb-4")

app.layout = dbc.Container([
    html.Div([
        html.H1("Mortalidad en Colombia, 2019"),
        html.P("Defunciones no fetales registradas por el DANE (Estadísticas Vitales). "
               "Usa los filtros o haz clic en un departamento del mapa."),
    ], className="encabezado"),
    panel_filtros,
    dbc.Row([
        dbc.Col(tarjeta_indicador("indicador-total", "Total de muertes"), md=4, className="mb-4"),
        dbc.Col(tarjeta_indicador("indicador-homicidios", "Homicidios por arma de fuego (X95)"), md=4, className="mb-4"),
        dbc.Col(tarjeta_indicador("indicador-mujeres", "Porcentaje de mujeres"), md=4, className="mb-4"),
    ]),
    dbc.Row([tarjeta_grafico("grafico-mapa", 6), tarjeta_grafico("grafico-meses", 6)]),
    dbc.Row([tarjeta_grafico("grafico-violentas", 6), tarjeta_grafico("grafico-menor", 6)]),
    dbc.Row([tabla_causas]),
    dbc.Row([tarjeta_grafico("grafico-sexo", 12)]),
    dbc.Row([tarjeta_grafico("grafico-edad", 12)]),
    html.Footer([
        html.P("Fuente: DANE, Estadísticas Vitales (EEVV) 2019 — defunciones no fetales.",
               className="mb-1"),
        html.P(f"Autores: {', '.join(AUTORES)} · Aplicaciones 1 (SMTART84, Grupo 2) · "
               "Maestría en Inteligencia Artificial, Universidad de La Salle", className="mb-0"),
    ], className="pie-pagina"),
], fluid=True)


@app.callback(
    Output("filtro-departamento", "value"),
    Output("filtro-sexo", "value"),
    Output("filtro-meses", "value"),
    Input("grafico-mapa", "clickData"),
    Input("boton-limpiar", "n_clicks"),
    State("filtro-sexo", "value"),
    State("filtro-meses", "value"),
    prevent_initial_call=True,
)
def actualizar_filtros(clic_mapa, _clics_limpiar, sexo, meses):
    """Clic en el mapa -> filtra por ese departamento; Limpiar -> restablece."""
    if ctx.triggered_id == "boton-limpiar":
        return datos.TODOS, datos.TODOS, [1, 12]
    departamento = clic_mapa["points"][0]["customdata"][0]
    return departamento, sexo, meses


@app.callback(
    Output("indicador-total", "children"),
    Output("indicador-homicidios", "children"),
    Output("indicador-mujeres", "children"),
    Output("grafico-mapa", "figure"),
    Output("grafico-meses", "figure"),
    Output("grafico-violentas", "figure"),
    Output("grafico-menor", "figure"),
    Output("tabla-causas", "data"),
    Output("grafico-sexo", "figure"),
    Output("grafico-edad", "figure"),
    Input("filtro-departamento", "value"),
    Input("filtro-sexo", "value"),
    Input("filtro-meses", "value"),
)
def actualizar_tablero(departamento, sexo, meses):
    muertes = datos.cargar_muertes()
    filtradas = datos.filtrar(muertes, departamento, sexo, meses)
    # El mapa y las barras por sexo ya muestran todos los departamentos:
    # no se filtran por departamento (solo se resalta el elegido).
    sin_filtro_depto = datos.filtrar(muertes, datos.TODOS, sexo, meses)
    sin_filtro_sexo = datos.filtrar(muertes, datos.TODOS, datos.TODOS, meses)
    seleccionado = None if departamento == datos.TODOS else departamento

    cifras = datos.indicadores(filtradas)
    tabla_sexo, orden = datos.muertes_por_sexo_y_departamento(sin_filtro_sexo)
    return (
        f"{cifras['total']:,}".replace(",", "."),
        f"{cifras['homicidios_arma']:,}".replace(",", "."),
        f"{cifras['porcentaje_mujeres']:.1f} %".replace(".", ","),
        graficos.mapa_departamentos(datos.muertes_por_departamento(sin_filtro_depto), seleccionado),
        graficos.lineas_por_mes(datos.muertes_por_mes(filtradas)),
        graficos.barras_ciudades_violentas(datos.ciudades_mas_violentas(filtradas)),
        graficos.circular_menor_mortalidad(datos.ciudades_menor_mortalidad(filtradas)),
        datos.principales_causas(filtradas).to_dict("records"),
        graficos.barras_apiladas_sexo(tabla_sexo, orden, seleccionado),
        graficos.histograma_edad(datos.muertes_por_categoria_edad(filtradas)),
    )


if __name__ == "__main__":
    app.run(debug=True)
