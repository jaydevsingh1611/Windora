from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config, service
from .models import AnalysisParams
from .repository import get_dataset

app = FastAPI(title="Day-ahead Wind Forecast API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

Params = Annotated[AnalysisParams, Query()]


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/meta")
def meta() -> dict:
    ds = get_dataset()
    return {
        "deliveryStart": config.DELIVERY_START.isoformat(),
        "deliveryEnd": config.DELIVERY_END.isoformat(),
        "defaultGate": config.DEFAULT_GATE.strftime("%H:%M"),
        "defaultHorizonH": config.DEFAULT_HORIZON_H,
        "maxHorizonH": config.MAX_HORIZON_H,
        "forecastRuns": len(ds.run_times),
        "dataSource": ds.source,
        "fetchedAt": ds.fetched_at,
    }


@app.get("/api/series")
def series(params: Params) -> dict:
    return service.series(get_dataset(), params.validated())


@app.get("/api/analysis")
def analysis(params: Params) -> dict:
    return service.analysis(get_dataset(), params.validated())


@app.get("/api/horizon-accuracy")
def horizon_accuracy(params: Params) -> dict:
    p = params.validated()
    return service.horizon_accuracy(get_dataset(), p.start, p.end)
