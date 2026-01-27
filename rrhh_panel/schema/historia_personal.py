# -*- coding: utf-8 -*-
from __future__ import annotations

# =============================================================================
# Contrato de datos — Historia Personal
# =============================================================================

REQUIRED_COLS = [
    "Código Personal",
    "Fecha Inicio Evento",
    "Fecha Fin Evento",
    "Fecha Nacimiento",
    "Clasificación",
    "Sexo",
    "TS_Responsable",
    "Empresa",
    "Área Original",
    "Cargo Actual",
    "Nacionalidad",
    "Lugar Registro",
    "Región Registro",
]

R_COL_CANDIDATES = ["%R", "% R", "R", "R%", "Porcentaje R", "PorcentajeR", "Factor R", "FactorR"]

COL_MAP = {
    "Código Personal": "cod",
    "Fecha Inicio Evento": "ini",
    "Fecha Fin Evento": "fin",
    "Fecha Nacimiento": "fnac",
    "Clasificación": "clas_raw",
    "Sexo": "sexo",
    "TS_Responsable": "ts",
    "Empresa": "emp",
    "Área Original": "area_raw",
    "Cargo Actual": "cargo",
    "Nacionalidad": "nac",
    "Lugar Registro": "lug",
    "Región Registro": "reg",
}

MISSING_LABEL = "SIN DATO"

KEEP_INTERNAL = [
    "cod", "ini", "fin", "fin_eff", "fnac",
    "r_pct",
    "clas_raw", "clas",
    "sexo", "ts", "emp",
    "area_raw", "area", "area_gen",
    "cargo", "nac", "lug", "reg",
]
