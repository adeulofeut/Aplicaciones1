"""Preparación de datos: convierte los Excel del DANE en un CSV liviano.

Se ejecuta una sola vez en local (no en el servidor):
    python scripts/preparar_datos.py

Lee los tres archivos de data/raw/, une las muertes con los nombres de
municipios, departamentos y causas, agrega la categoría de edad y guarda
data/mortalidad_2019.csv.gz con solo las columnas que usa la aplicación.
"""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_RAW = RAIZ / "data" / "raw"
ARCHIVO_SALIDA = RAIZ / "data" / "mortalidad_2019.csv.gz"

ARCHIVO_MUERTES = CARPETA_RAW / "Anexo1.NoFetal2019_CE_15-03-23.xlsx"
ARCHIVO_CODIGOS = CARPETA_RAW / "Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx"
ARCHIVO_DIVIPOLA = CARPETA_RAW / "Divipola_CE_.xlsx"

TOTAL_ESPERADO = 244_355  # filas de la hoja No_Fetales_2019

# Categorías de edad definidas en el enunciado (códigos DANE de GRUPO_EDAD1).
CATEGORIAS_EDAD = [
    ("Mortalidad neonatal", range(0, 5)),
    ("Mortalidad infantil", range(5, 7)),
    ("Primera infancia", range(7, 9)),
    ("Niñez", range(9, 11)),
    ("Adolescencia", range(11, 12)),
    ("Juventud", range(12, 14)),
    ("Adultez temprana", range(14, 17)),
    ("Adultez intermedia", range(17, 20)),
    ("Vejez", range(20, 25)),
    ("Longevidad / Centenarios", range(25, 29)),
    ("Edad desconocida", range(29, 30)),
]

SEXOS = {"1": "Hombre", "2": "Mujer", "3": "Indeterminado"}

# Nombres cortos para que los ejes de los gráficos sean legibles.
NOMBRES_CORTOS_DEPTO = {
    "BOGOTÁ, D.C.": "BOGOTÁ D.C.",
    "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA": "SAN ANDRÉS",
}


def categoria_edad(codigo):
    """Devuelve la categoría de edad correspondiente a un código GRUPO_EDAD1."""
    for nombre, codigos in CATEGORIAS_EDAD:
        if int(codigo) in codigos:
            return nombre
    raise ValueError(f"GRUPO_EDAD1 fuera de la tabla del enunciado: {codigo}")


def leer_muertes():
    """Lee los registros de defunciones no fetales de 2019."""
    columnas = ["COD_DANE", "COD_DEPARTAMENTO", "MES", "SEXO", "GRUPO_EDAD1",
                "MANERA_MUERTE", "COD_MUERTE"]
    muertes = pd.read_excel(ARCHIVO_MUERTES, sheet_name="No_Fetales_2019",
                            dtype=str, usecols=columnas)
    return muertes.apply(lambda columna: columna.str.strip())


def leer_divipola():
    """Lee la hoja con valores (Hoja3); Hoja1 contiene fórmulas de Excel."""
    divipola = pd.read_excel(ARCHIVO_DIVIPOLA, sheet_name="Hoja3", skiprows=2,
                             header=None, dtype=str)
    divipola.columns = ["COD_DEPARTAMENTO", "DEPARTAMENTO", "COD_DANE",
                        "MUNICIPIO", "TIPO", "LONGITUD", "LATITUD"]
    divipola = divipola.apply(lambda columna: columna.str.strip())
    # Las coordenadas vienen como texto con coma decimal ("-75,581775").
    for columna in ["LONGITUD", "LATITUD"]:
        divipola[columna] = pd.to_numeric(divipola[columna].str.replace(",", "."))
    divipola["DEPARTAMENTO"] = divipola["DEPARTAMENTO"].replace(NOMBRES_CORTOS_DEPTO)
    return divipola


def leer_causas():
    """Arma un diccionario código CIE-10 -> descripción (3 y 4 caracteres)."""
    codigos = pd.read_excel(ARCHIVO_CODIGOS, sheet_name="Final", skiprows=8,
                            dtype=str).iloc[:, :6]
    codigos.columns = ["CAPITULO", "NOMBRE_CAPITULO", "COD3", "DESC3", "COD4", "DESC4"]
    codigos = codigos.dropna(subset=["COD3"]).apply(lambda columna: columna.str.strip())
    tres = codigos.drop_duplicates("COD3").set_index("COD3")["DESC3"]
    cuatro = codigos.dropna(subset=["COD4"]).set_index("COD4")["DESC4"]
    # Los datos usan el código de 4 caracteres y, a veces, solo el de 3.
    return pd.concat([cuatro, tres]).to_dict()


def preparar():
    muertes = leer_muertes()
    assert len(muertes) == TOTAL_ESPERADO, f"Se esperaban {TOTAL_ESPERADO} filas, hay {len(muertes)}"

    divipola = leer_divipola()
    departamentos = divipola.drop_duplicates("COD_DEPARTAMENTO").set_index("COD_DEPARTAMENTO")["DEPARTAMENTO"]
    municipios = divipola.set_index("COD_DANE")["MUNICIPIO"]

    datos = pd.DataFrame({
        "cod_dane": muertes["COD_DANE"],
        "cod_departamento": muertes["COD_DEPARTAMENTO"],
        "departamento": muertes["COD_DEPARTAMENTO"].map(departamentos),
        "municipio": muertes["COD_DANE"].map(municipios),
        "mes": muertes["MES"].astype(int),
        "sexo": muertes["SEXO"].map(SEXOS),
        "grupo_edad": muertes["GRUPO_EDAD1"].astype(int),
        "categoria_edad": muertes["GRUPO_EDAD1"].map(categoria_edad),
        "manera_muerte": muertes["MANERA_MUERTE"],
        "cod_muerte": muertes["COD_MUERTE"],
        "causa": muertes["COD_MUERTE"].map(leer_causas()),
    })

    # Municipios que no están en la Divipola (p. ej. 94663, antiguo
    # corregimiento de Guainía): se conserva el registro con su código.
    sin_municipio = datos["municipio"].isna()
    datos.loc[sin_municipio, "municipio"] = "Código " + datos.loc[sin_municipio, "cod_dane"]

    # Validaciones: nada se pierde ni queda sin nombre.
    assert len(datos) == TOTAL_ESPERADO
    for columna in ["departamento", "sexo", "categoria_edad", "causa"]:
        faltantes = datos[columna].isna().sum()
        assert faltantes == 0, f"{faltantes} registros sin {columna}"

    datos.to_csv(ARCHIVO_SALIDA, index=False, compression="gzip")

    # Coordenadas medias por departamento (respaldo para el mapa de burbujas).
    centros = (divipola.groupby(["COD_DEPARTAMENTO", "DEPARTAMENTO"], as_index=False)
               [["LATITUD", "LONGITUD"]].mean())
    centros.columns = ["cod_departamento", "departamento", "latitud", "longitud"]
    centros.to_csv(RAIZ / "data" / "departamentos.csv", index=False)

    print(f"Registros: {len(datos):,}")
    print(f"Municipios sin nombre en Divipola: {sin_municipio.sum()}")
    print(f"Archivo: {ARCHIVO_SALIDA} ({ARCHIVO_SALIDA.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    preparar()
