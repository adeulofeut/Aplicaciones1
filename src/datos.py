"""Carga, filtros y agregaciones de los datos de mortalidad (sin Dash).

Cada función recibe un DataFrame (ya filtrado) y devuelve la tabla que
necesita un gráfico. Así la lógica se puede probar sin la interfaz.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

CARPETA_DATOS = Path(__file__).resolve().parent.parent / "data"

TODOS = "Todos"

# Orden natural (por edad) de las categorías del enunciado.
ORDEN_EDAD = [
    "Mortalidad neonatal", "Mortalidad infantil", "Primera infancia", "Niñez",
    "Adolescencia", "Juventud", "Adultez temprana", "Adultez intermedia",
    "Vejez", "Longevidad / Centenarios", "Edad desconocida",
]

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# Homicidios del enunciado: X95 = agresión con disparo de otras armas de
# fuego y las no especificadas (X950–X959).
PREFIJO_HOMICIDIO_ARMA = "X95"


@lru_cache(maxsize=1)
def cargar_muertes():
    """Lee el CSV preparado por scripts/preparar_datos.py (una sola vez)."""
    return pd.read_csv(CARPETA_DATOS / "mortalidad_2019.csv.gz",
                       dtype={"cod_dane": str, "cod_departamento": str})


@lru_cache(maxsize=1)
def cargar_departamentos():
    """Coordenadas medias por departamento, para el mapa."""
    return pd.read_csv(CARPETA_DATOS / "departamentos.csv",
                       dtype={"cod_departamento": str})


def lista_departamentos():
    return sorted(cargar_muertes()["departamento"].unique())


def filtrar(muertes, departamento=TODOS, sexo=TODOS, meses=(1, 12)):
    """Aplica los filtros del panel; "Todos" deja pasar todo."""
    condicion = muertes["mes"].between(meses[0], meses[1])
    if departamento and departamento != TODOS:
        condicion &= muertes["departamento"] == departamento
    if sexo and sexo != TODOS:
        condicion &= muertes["sexo"] == sexo
    return muertes[condicion]


def muertes_por_departamento(muertes):
    """Total de muertes por departamento, con coordenadas para el mapa."""
    totales = muertes.groupby("cod_departamento").size().rename("muertes").reset_index()
    return cargar_departamentos().merge(totales, on="cod_departamento", how="left").fillna({"muertes": 0})


def muertes_por_mes(muertes):
    """Total de muertes en cada mes; los meses sin datos quedan en 0."""
    totales = muertes.groupby("mes").size().reindex(range(1, 13), fill_value=0)
    return pd.DataFrame({"mes": MESES, "muertes": totales.values})


def ciudades_mas_violentas(muertes, cantidad=5):
    """Municipios con más homicidios por arma de fuego (código X95)."""
    homicidios = muertes[muertes["cod_muerte"].str.startswith(PREFIJO_HOMICIDIO_ARMA)]
    return (homicidios.groupby(["municipio", "departamento"]).size()
            .rename("homicidios").reset_index()
            .sort_values("homicidios", ascending=False).head(cantidad))


def ciudades_menor_mortalidad(muertes, cantidad=10):
    """Municipios con menos muertes registradas (conteo absoluto).

    Solo cuenta municipios con al menos una muerte y con nombre en la
    Divipola; los empates se resuelven por orden alfabético para que el
    resultado sea estable.
    """
    con_nombre = muertes[~muertes["municipio"].str.startswith("Código ")]
    return (con_nombre.groupby(["municipio", "departamento"]).size()
            .rename("muertes").reset_index()
            .sort_values(["muertes", "municipio"]).head(cantidad))


def principales_causas(muertes, cantidad=10):
    """Las causas de muerte (código CIE-10) con más casos."""
    return (muertes.groupby(["cod_muerte", "causa"]).size()
            .rename("total").reset_index()
            .sort_values("total", ascending=False).head(cantidad))


def muertes_por_sexo_y_departamento(muertes):
    """Tabla departamento × sexo, ordenada por total de muertes."""
    tabla = muertes.groupby(["departamento", "sexo"]).size().rename("muertes").reset_index()
    orden = tabla.groupby("departamento")["muertes"].sum().sort_values(ascending=False).index
    return tabla, list(orden)


def muertes_por_categoria_edad(muertes):
    """Muertes en cada categoría de edad, en orden de edad."""
    totales = muertes["categoria_edad"].value_counts().reindex(ORDEN_EDAD, fill_value=0)
    return pd.DataFrame({"categoria_edad": ORDEN_EDAD, "muertes": totales.values})


def indicadores(muertes):
    """Cifras resumen para las tarjetas superiores."""
    total = len(muertes)
    homicidios = muertes["cod_muerte"].str.startswith(PREFIJO_HOMICIDIO_ARMA).sum()
    mujeres = (muertes["sexo"] == "Mujer").sum()
    return {
        "total": total,
        "homicidios_arma": int(homicidios),
        "porcentaje_mujeres": mujeres / total * 100 if total else 0,
    }
