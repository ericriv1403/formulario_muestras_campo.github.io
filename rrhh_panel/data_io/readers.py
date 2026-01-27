# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd

from rrhh_panel.schema.historia_personal import REQUIRED_COLS, R_COL_CANDIDATES

def read_excel_any(file_obj_or_path, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(file_obj_or_path, sheet_name=sheet_name)

def read_excel_strict_hist(file_obj_or_path, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(file_obj_or_path, sheet_name=sheet_name)
    cols = list(df.columns)
    r_col = next((c for c in cols if str(c).strip() in R_COL_CANDIDATES), None)
    keep = [c for c in REQUIRED_COLS if c in cols]
    if r_col and r_col not in keep:
        keep.append(r_col)
    return df[keep].copy() if keep else df.copy()

def read_csv_any(file_obj_or_path) -> pd.DataFrame:
    return pd.read_csv(file_obj_or_path)
