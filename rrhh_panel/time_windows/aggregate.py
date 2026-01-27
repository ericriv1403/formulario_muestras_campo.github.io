# -*- coding: utf-8 -*-
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from rrhh_panel.utils.dates import add_calendar_fields

@st.cache_data(show_spinner=False)
def aggregate_daily_to_period_simple(df_daily: pd.DataFrame, period: str) -> pd.DataFrame:
    d = df_daily.copy()
    if "CodSem" not in d.columns or "CodMes" not in d.columns or "Año" not in d.columns:
        d = add_calendar_fields(d, "Día")

    key = {"D": "Día", "W": "CodSem", "M": "CodMes", "Y": "Año"}[period]
    cut_col = {"D": "Día", "W": "FinSemana", "M": "FinMes", "Y": "Día"}[period]

    def _agg(g: pd.DataFrame) -> pd.Series:
        ws = g["Día"].min()
        we = g["Día"].max()
        cut = g[cut_col].max() if cut_col in g.columns else we
        sal = float(np.nansum(g["Salidas"].astype(float).values)) if "Salidas" in g.columns else 0.0
        exist_prom = float(np.nanmean(g["Existencias"].astype(float).values)) if "Existencias" in g.columns else np.nan
        return pd.Series({
            "window_start": ws,
            "window_end": we,
            "cut": cut,
            "Salidas": sal,
            "Existencias_Prom": exist_prom,
        })

    out = d.groupby(key, dropna=False, as_index=False).apply(_agg).reset_index(drop=True)

    if period == "D":
        out["Periodo"] = pd.to_datetime(out["window_start"]).dt.strftime("%Y-%m-%d")
    elif period in ("W", "M"):
        out["Periodo"] = out[key].astype(str)
    else:
        out["Periodo"] = out[key].astype(int).astype(str)

    out = out.sort_values("cut").reset_index(drop=True)
    return out[["Periodo", "cut", "window_start", "window_end", "Salidas", "Existencias_Prom"]]
