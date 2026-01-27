# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd

def safe_table_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c) for c in out.columns]
    return out
