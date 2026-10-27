from __future__ import annotations

from datetime import date, time

from fastapi import HTTPException
from pydantic import BaseModel

from . import config
from .forecast import Mode


class AnalysisParams(BaseModel):
    start: date = config.DELIVERY_START
    end: date = config.DELIVERY_END
    mode: Mode = "gate"
    gate: time = config.DEFAULT_GATE
    horizon: float = config.DEFAULT_HORIZON_H

    def validated(self) -> "AnalysisParams":
        if self.start > self.end:
            raise HTTPException(422, "start must be on or before end")
        if self.start < config.DELIVERY_START or self.end > config.DELIVERY_END:
            raise HTTPException(
                422,
                f"delivery days must be within {config.DELIVERY_START} and {config.DELIVERY_END}",
            )
        if not 0 <= self.horizon <= config.MAX_HORIZON_H:
            raise HTTPException(422, f"horizon must be between 0 and {config.MAX_HORIZON_H:g} hours")
        return self
