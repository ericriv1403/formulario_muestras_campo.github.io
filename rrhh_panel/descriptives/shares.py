# -*- coding: utf-8 -*-
from __future__ import annotations

import numpy as np
import pandas as pd

from rrhh_panel.schema.historia_personal import MISSING_LABEL
from rrhh_panel.descriptives.topn import topn_otros_multi

def compute_exit_share_of_total_existences(
    df_now: pd.DataFrame,
    df_exit: pd.DataFrame,
    dim_col: str,
    topn: int,
    total_exist_base: float,
) -> pd.DataFrame:
    if df_exit is None or df_exit.empty:
        return pd.DataFrame(columns=["Categoria", "Salidas", "PctTotalExist", "ExistSnapshot", "TasaSobreArea"])
    if df_now is None or df_now.empty or total_exist_base is None or (isinstance(total_exist_base, float) and np.isnan(total_exist_base)) or total_exist_base <= 0:
        total_exist_base = float(len(df_now)) if (df_now is not None) else np.nan

    ex = df_exit.copy()
    ex[dim_col] = ex[dim_col].fillna(MISSING_LABEL).astype(str)
    g_exit = ex.groupby(dim_col)["cod"].nunique().rename("Salidas").reset_index().rename(columns={dim_col: "Categoria"})

    now = df_now.copy()
    now[dim_col] = now[dim_col].fillna(MISSING_LABEL).astype(str)
    g_now = now.groupby(dim_col)["cod"].nunique().rename("ExistSnapshot").reset_index().rename(columns={dim_col: "Categoria"})

    d = g_exit.merge(g_now, on="Categoria", how="left")
    d["ExistSnapshot"] = d["ExistSnapshot"].fillna(0).astype(int)

    d["PctTotalExist"] = (d["Salidas"] / float(total_exist_base)) * 100.0 if total_exist_base and total_exist_base > 0 else np.nan
    d["TasaSobreArea"] = np.where(d["ExistSnapshot"] > 0, (d["Salidas"] / d["ExistSnapshot"]) * 100.0, np.nan)

    d = topn_otros_multi(d, cat_col="Categoria", sort_col="Salidas", topn=topn)
    d = d.sort_values("PctTotalExist", ascending=True).reset_index(drop=True)
    return d
