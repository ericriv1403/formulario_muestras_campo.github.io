# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List
import pandas as pd

def options_for_col(df: pd.DataFrame, col: str) -> List[str]:
    v = df[col].dropna().astype(str).str.strip()
    v = v[v != ""].unique().tolist()
    return sorted(v)
