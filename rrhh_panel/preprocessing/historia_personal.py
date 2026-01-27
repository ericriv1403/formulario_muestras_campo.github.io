# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Tuple, Dict, Any, List
import numpy as np
import pandas as pd
import streamlit as st

from rrhh_panel.schema.historia_personal import REQUIRED_COLS, R_COL_CANDIDATES, COL_MAP, KEEP_INTERNAL, MISSING_LABEL
from rrhh_panel.references.areas import AREA_REF
from rrhh_panel.references.clasificacion import CLAS_REF
from rrhh_panel.utils.dates import to_datetime_norm, today_dt

# =============================================================================
# Mapping Área y Clasificación
# =============================================================================
def map_area(area_raw: pd.Series) -> Tuple[pd.Series, pd.Series]:
    key = area_raw.astype("string").str.strip()
    key_u = key.str.upper()

    std = key_u.map(lambda x: AREA_REF.get(x, (None, None))[0] if pd.notna(x) else None)
    gen = key_u.map(lambda x: AREA_REF.get(x, (None, None))[1] if pd.notna(x) else None)

    std = std.fillna(key).replace({"": pd.NA}).fillna(MISSING_LABEL).astype("string")
    gen = gen.fillna(pd.NA).replace({"": pd.NA}).fillna(MISSING_LABEL).astype("string")
    return std, gen

def map_clas(clas_raw: pd.Series) -> pd.Series:
    key = clas_raw.astype("string").str.strip()
    key_u = key.str.upper()
    std = key_u.map(lambda x: CLAS_REF.get(x, None) if pd.notna(x) else None)
    std = std.fillna(key).replace({"": pd.NA}).fillna(MISSING_LABEL).astype("string")
    return std

# =============================================================================
# Preparación de Historia Personal
# =============================================================================
@st.cache_data(show_spinner=False)
def validate_and_prepare_hist(df_raw: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLS if c not in df_raw.columns]
    if missing:
        raise ValueError("Faltan columnas requeridas en Historia Personal:\n- " + "\n- ".join(missing))

    cols = list(df_raw.columns)
    r_col = next((c for c in cols if str(c).strip() in R_COL_CANDIDATES), None)

    use_cols = REQUIRED_COLS.copy()
    if r_col and r_col not in use_cols:
        use_cols.append(r_col)

    df = df_raw[use_cols].copy()
    out = df.rename(columns=COL_MAP)

    out["ini"] = to_datetime_norm(out["ini"])
    out["fin"] = to_datetime_norm(out["fin"])
    out["fnac"] = to_datetime_norm(out["fnac"])
    out["fin_eff"] = out["fin"].fillna(today_dt())

    if r_col:
        out = out.rename(columns={r_col: "r_pct"})
    else:
        out["r_pct"] = 1.0

    for c in ["cod", "clas_raw", "sexo", "ts", "emp", "area_raw", "cargo", "nac", "lug", "reg"]:
        out[c] = out[c].astype("string").str.strip()
        out.loc[out[c].isin(["", "None", "nan", "NaT"]), c] = pd.NA

    out = out[~out["cod"].isna()].copy()
    out = out[~out["ini"].isna()].copy()
    out["cod"] = out["cod"].astype(str)

    rp = out["r_pct"].copy()
    if rp.dtype == "object" or str(rp.dtype).startswith("string"):
        rp2 = rp.astype(str).str.replace("%", "", regex=False).str.strip()
        rp_num = pd.to_numeric(rp2, errors="coerce")
        rp_num = np.where(rp_num > 1.5, rp_num / 100.0, rp_num)
        out["r_pct"] = pd.Series(rp_num, index=out.index).fillna(1.0).astype(float)
    else:
        rp_num = pd.to_numeric(rp, errors="coerce").fillna(1.0).astype(float)
        rp_num = np.where(rp_num > 1.5, rp_num / 100.0, rp_num)
        out["r_pct"] = rp_num

    out["area"], out["area_gen"] = map_area(out["area_raw"])
    out["clas"] = map_clas(out["clas_raw"])

    out = out[KEEP_INTERNAL].copy()
    out = out.sort_values(["cod", "ini", "fin_eff"]).reset_index(drop=True)
    return out

# =============================================================================
# Intervalos por persona (para existencias diarias y KPI)
# =============================================================================
@st.cache_data(show_spinner=False)
def merge_intervals_per_person(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[pd.Series] = []
    for cod, g in df.groupby("cod", sort=False):
        g = g.sort_values(["ini", "fin_eff"]).copy()
        cur_ini = None
        cur_fin = None
        cur_row = None

        for _, r in g.iterrows():
            ini = r["ini"]
            fin = r["fin_eff"]
            if cur_ini is None:
                cur_ini, cur_fin = ini, fin
                cur_row = r
                continue

            if ini <= (cur_fin + pd.Timedelta(days=1)):
                if fin > cur_fin:
                    cur_fin = fin
                cur_row = r
            else:
                out_r = cur_row.copy()
                out_r["ini"] = cur_ini
                out_r["fin_eff"] = cur_fin
                rows.append(out_r)

                cur_ini, cur_fin = ini, fin
                cur_row = r

        if cur_ini is not None:
            out_r = cur_row.copy()
            out_r["ini"] = cur_ini
            out_r["fin_eff"] = cur_fin
            rows.append(out_r)

    return pd.DataFrame(rows).reset_index(drop=True)
