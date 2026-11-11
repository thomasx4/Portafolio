import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_PATH = os.path.join(BASE_DIR, "data", "portafolio.xlsx")

# Nombres exactos de columnas en la hoja PRECIOS (tal como vienen en el Excel)
COLUMNAS_ACTIVOS = {
    "PROM": "PROMIGAS",
    "PFCIBEST - COP": "PFCIBEST",
    "ISA - COP": "ISA",
    "J&J": "J&J",
    "XOM": "XOM",
    "AAPL": "AAPL",
    "SPY": "SPY",
    "QQQ": "QQQ",
    "VEA": "VEA",
    "GLD": "GLD",
}


def cargar_precios():
    """
    Lee la hoja PRECIOS del Excel y devuelve un DataFrame limpio
    con índice de fechas y columnas renombradas.
    """
    # La hoja se llama "PRECIOS " (con espacio al final). Probamos varias variantes.
    hojas_posibles = ["PRECIOS ", "PRECIOS", "Precios"]
    df = None
    for hoja in hojas_posibles:
        try:
            df = pd.read_excel(EXCEL_PATH, sheet_name=hoja, header=0)
            break
        except ValueError:
            continue

    if df is None:
        raise ValueError("No se encontró la hoja PRECIOS en el Excel.")

    # La primera fila de datos del Excel tiene 'Fecha' como encabezado de la columna A
    df.columns = [str(c).strip() for c in df.columns]

    # Eliminar filas sin fecha (por ejemplo, filas de totales al final)
    df = df.dropna(subset=["Fecha"])

    # Convertir fecha
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha"])
    df = df.set_index("Fecha").sort_index()

    # Seleccionar solo activos reales y renombrar
    columnas_existentes = [c for c in COLUMNAS_ACTIVOS.keys() if c in df.columns]
    df = df[columnas_existentes].copy()

    # Convertir a numérico (por si vienen como texto o con comas)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.rename(columns=COLUMNAS_ACTIVOS)
    df = df.dropna(how="any")
    return df


def calcular_rendimientos(df_precios):
    """
    Recalcula los rendimientos logarítmicos a partir de los precios.
    Fórmula: r_t = LN(P_t / P_{t-1})
    """
    df_rend = np.log(df_precios / df_precios.shift(1)).dropna()
    return df_rend


def cargar_todo():
    """Devuelve precios y rendimientos listos para usar."""
    precios = cargar_precios()
    rendimientos = calcular_rendimientos(precios)
    return precios, rendimientos