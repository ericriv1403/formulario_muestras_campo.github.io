# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd
from rrhh_panel.schema.historia_personal import MISSING_LABEL

def counts_topn_with_otros(s: pd.Series, topn: int = 10) -> pd.DataFrame:
    x = s.fillna(MISSING_LABEL).astype(str)
    vc = x.value_counts(dropna=False)
    if vc.empty:
        return pd.DataFrame(columns=["Categoria", "N"])
    if len(vc) <= topn:
        df = vc.reset_index()
        df.columns = ["Categoria", "N"]
        return df
    top = vc.head(topn)
    otros = vc.iloc[topn:].sum()
    df = top.reset_index()
    df.columns = ["Categoria", "N"]
    df = pd.concat([df, pd.DataFrame([{"Categoria": "OTROS", "N": int(otros)}])], ignore_index=True)
    return df

def topn_otros_multi(df: pd.DataFrame, cat_col: str, sort_col: str, topn: int) -> pd.DataFrame:
    d = df.copy()
    d[cat_col] = d[cat_col].fillna(MISSING_LABEL).astype(str)
    d = d.sort_values(sort_col, ascending=False)
    if len(d) <= topn:
        return d
    top = d.head(topn).copy()
    rest = d.iloc[topn:].copy()
    agg = {c: "sum" for c in d.columns if c != cat_col}
    otros = rest.agg(agg).to_dict()
    otros[cat_col] = "OTROS"
    out = pd.concat([top, pd.DataFrame([otros])], ignore_index=True)
    return out
