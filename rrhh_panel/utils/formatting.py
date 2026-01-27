# -*- coding: utf-8 -*-
from __future__ import annotations

import numpy as np

def fmt_es(x: float, dec: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_int_es(x: float) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{int(round(x)):,}".replace(",", ".")
