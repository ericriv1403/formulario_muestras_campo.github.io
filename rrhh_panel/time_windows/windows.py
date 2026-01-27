# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd
from rrhh_panel.utils.dates import add_calendar_fields

def build_period_windows(start: pd.Timestamp, end: pd.Timestamp, period: str) -> pd.DataFrame:
    days = pd.date_range(start, end, freq="D")
    cal = add_calendar_fields(pd.DataFrame({"Día": days}), "Día")

    if period == "D":
        w = cal[["Día"]].copy()
        w["window_start"] = w["Día"]
        w["window_end"] = w["Día"]
        w["cut"] = w["Día"]
        w["Periodo"] = w["Día"].dt.strftime("%Y-%m-%d")
        return w[["Periodo", "cut", "window_start", "window_end"]]

    if period == "W":
        w = cal.groupby("CodSem", as_index=False).agg(
            window_start=("Día", "min"),
            window_end=("Día", "max"),
            cut=("FinSemana", "max"),
        )
        w["Periodo"] = w["CodSem"].astype(str)
        return w[["Periodo", "cut", "window_start", "window_end"]].sort_values("cut")

    if period == "M":
        w = cal.groupby("CodMes", as_index=False).agg(
            window_start=("Día", "min"),
            window_end=("Día", "max"),
            cut=("FinMes", "max"),
        )
        w["Periodo"] = w["CodMes"].astype(str)
        return w[["Periodo", "cut", "window_start", "window_end"]].sort_values("cut")

    if period == "Y":
        w = cal.groupby("Año", as_index=False).agg(
            window_start=("Día", "min"),
            window_end=("Día", "max"),
            cut=("Día", "max"),
        )
        w["Periodo"] = w["Año"].astype(int).astype(str)
        return w[["Periodo", "cut", "window_start", "window_end"]].sort_values("cut")

    raise ValueError("period inválido")
