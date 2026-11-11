from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_loader import cargar_todo
from core.analysis import estadisticas, matrices, simular_portafolios, portafolio_optimo

app = FastAPI(title="Portafolio Quindío 2026")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ---- Carga global de datos ----
try:
    PRECIOS, RENDIMIENTOS = cargar_todo()
    print(f"[OK] Datos cargados: {len(PRECIOS)} filas, {len(PRECIOS.columns)} activos")
    ESTAD = estadisticas(RENDIMIENTOS)
    COV, CORR = matrices(RENDIMIENTOS)
    SIMULACION, ACTIVOS = simular_portafolios(RENDIMIENTOS, n_portafolios=3000)
    OPTIMO = portafolio_optimo(SIMULACION)
except Exception as e:
    print(f"[ERROR] Falló la carga del Excel: {e}")
    PRECIOS = RENDIMIENTOS = ESTAD = COV = CORR = SIMULACION = OPTIMO = None
    ACTIVOS = []


# ---------------------- VISTAS ----------------------
@app.get("/", response_class=HTMLResponse)
async def portada(request: Request):
    return templates.TemplateResponse("portada.html", {"request": request})


@app.get("/precios", response_class=HTMLResponse)
async def vista_precios(request: Request):
    if PRECIOS is None:
        return HTMLResponse("<h1>No se pudo cargar el Excel</h1>", status_code=500)
    df = PRECIOS.copy()
    df.index = df.index.strftime("%Y-%m-%d")
    return templates.TemplateResponse("precios.html", {
        "request": request,
        "columnas": df.columns.tolist(),
        "filas": df.reset_index().values.tolist(),
        "fechas": df.index.tolist(),
    })


@app.get("/rendimientos", response_class=HTMLResponse)
async def vista_rendimientos(request: Request):
    if RENDIMIENTOS is None:
        return HTMLResponse("<h1>No se pudo cargar el Excel</h1>", status_code=500)

    return templates.TemplateResponse("rendimientos.html", {
        "request": request,
        "activos": ACTIVOS,
        "media_a": ESTAD["Media_Anual"].tolist(),
        "vol_a": ESTAD["Vol_Anual"].tolist(),
        "fechas": RENDIMIENTOS.index.strftime("%Y-%m-%d").tolist(),
        "datos": RENDIMIENTOS.round(4).values.tolist(),
    })


@app.get("/cov-cor", response_class=HTMLResponse)
async def vista_cov_cor(request: Request):
    if COV is None:
        return HTMLResponse("<h1>No se pudo cargar el Excel</h1>", status_code=500)
    return templates.TemplateResponse("cov_cor.html", {
        "request": request,
        "activos": ACTIVOS,
        "cov_matrix": COV.round(4).values.tolist(),
        "corr_matrix": CORR.round(4).values.tolist(),
    })


@app.get("/frontera", response_class=HTMLResponse)
async def vista_frontera(request: Request):
    if SIMULACION is None:
        return HTMLResponse("<h1>No se pudo cargar el Excel</h1>", status_code=500)

    # Preparar lista de pares (activo, peso) ya resuelta en Python
    pares_pesos = [
        {"activo": a, "peso": round(float(p), 4)}
        for a, p in zip(ACTIVOS, OPTIMO["pesos"])
    ]

    return templates.TemplateResponse("frontera.html", {
        "request": request,
        "activos": ACTIVOS,
        "riesgos": SIMULACION["riesgo"].round(4).tolist(),
        "retornos": SIMULACION["retorno"].round(4).tolist(),
        "sharpes": SIMULACION["sharpe"].round(4).tolist(),
        "optimo": {
            "retorno": round(float(OPTIMO["retorno"]), 4),
            "riesgo": round(float(OPTIMO["riesgo"]), 4),
            "sharpe": round(float(OPTIMO["sharpe"]), 4),
            "pares_pesos": pares_pesos,
        },
    })

# ---------------------- API JSON (opcional) ----------------------
@app.get("/api/estadisticas")
async def api_estadisticas():
    if ESTAD is None:
        return JSONResponse({"error": "Datos no cargados"}, status_code=500)
    return ESTAD.to_dict(orient="index")