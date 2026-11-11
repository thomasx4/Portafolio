import numpy as np
import pandas as pd


def estadisticas(df_rendimientos):
    """
    Devuelve DataFrame con media mensual, media anual,
    volatilidad mensual y volatilidad anual por activo.
    """
    media_m = df_rendimientos.mean()
    media_a = media_m * 12
    vol_m = df_rendimientos.std()
    vol_a = vol_m * np.sqrt(12)

    return pd.DataFrame({
        "Media_Mensual": media_m,
        "Media_Anual": media_a,
        "Vol_Mensual": vol_m,
        "Vol_Anual": vol_a,
    }).round(4)


def matrices(df_rendimientos):
    """Devuelve (covarianza, correlación)."""
    return df_rendimientos.cov(), df_rendimientos.corr()


def simular_portafolios(df_rendimientos, n_portafolios=3000, rf=0.0486, seed=42):
    """
    Simula n portafolios aleatorios con pesos que suman 1.
    Devuelve DataFrame con pesos, retorno anual, riesgo anual y Sharpe.
    """
    np.random.seed(seed)
    activos = df_rendimientos.columns.tolist()
    n_activos = len(activos)

    media_m = df_rendimientos.mean()
    cov_m = df_rendimientos.cov()

    ret_anual = (media_m * 12).values
    cov_anual = (cov_m * 12).values

    resultados = []
    for _ in range(n_portafolios):
        pesos = np.random.random(n_activos)
        pesos /= pesos.sum()

        ret_p = float(np.dot(pesos, ret_anual))
        var_p = float(np.dot(pesos.T, np.dot(cov_anual, pesos)))
        risk_p = np.sqrt(var_p)
        sharpe = (ret_p - rf) / risk_p if risk_p > 0 else 0.0

        resultados.append({
            "pesos": pesos.tolist(),
            "retorno": ret_p,
            "riesgo": risk_p,
            "sharpe": sharpe,
        })

    return pd.DataFrame(resultados), activos


def portafolio_optimo(df_simulacion):
    """Devuelve la fila del portafolio con mayor Sharpe."""
    idx = df_simulacion["sharpe"].idxmax()
    return df_simulacion.loc[idx]