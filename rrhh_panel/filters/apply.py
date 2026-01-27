# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd
from rrhh_panel.filters.state import FilterState

def apply_categorical_filters(df: pd.DataFrame, fs: FilterState) -> pd.DataFrame:
    out = df.copy()

    def _apply(col: str, selected: list[str]) -> None:
        nonlocal out
        if selected:
            out = out[out[col].isin(selected)]

    _apply("sexo", fs.sexo)
    _apply("area_gen", fs.area_gen)
    _apply("area", fs.area)
    _apply("cargo", fs.cargo)
    _apply("clas", fs.clas)
    _apply("ts", fs.ts)
    _apply("emp", fs.emp)
    _apply("nac", fs.nac)
    _apply("lug", fs.lug)
    _apply("reg", fs.reg)
    return out
