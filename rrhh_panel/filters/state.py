# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import List

@dataclass
class FilterState:
    sexo: List[str]
    area_gen: List[str]
    area: List[str]
    cargo: List[str]
    clas: List[str]
    ts: List[str]
    emp: List[str]
    nac: List[str]
    lug: List[str]
    reg: List[str]
    antig: List[str]
    edad: List[str]
