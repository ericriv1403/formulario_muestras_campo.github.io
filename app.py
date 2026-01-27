# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


# =============================================================================
# 0) TÍTULOS / TEXTOS
# =============================================================================
APP_TITLE = "Panel RRHH (Limpio)"
APP_SUBTITLE = "Existencias • Salidas • (1 - Supervivencia 30 días) + Meta (promedio 3 últimos registros del año pasado)"

LBL_SHOW_FILTERS = "Mostrar panel (cargar datos / filtros / opciones)"
LBL_VIEW_PICK = "Vista"
VIEW_1 = "Dashboard"
VIEW_2 = "Descriptivos (Existencias & Salidas)"

PANEL_TITLE = "Panel de control"
TAB_DATA = "Datos & Periodo"
TAB_FILTERS = "Filtros"
TAB_OPTIONS = "Opciones"

LBL_UPLOAD_MAIN = "Sube Excel/CSV (Historia Personal)"
LBL_PATH_MAIN = "O ruta local (opcional)"
LBL_SHEET_MAIN = "Hoja (Historia Personal)"

LBL_RANGE_PRESET = "Atajo de rango"
LBL_RANGE_SLIDER = "Inicio / Fin"
LBL_GROUP_BY = "Agrupar por"
LBL_SNAPSHOT_DATE = "Snapshot (día)"
LBL_TODAY_CUT = "Hoy (corte)"

LBL_FILTERS_HINT = "Deja vacío = no filtra (equivale a TODOS)."
BTN_CLEAR_FILTERS = "Limpiar filtros"

LBL_SEXO = "Sexo"
LBL_AREA_GEN = "Área General"
LBL_AREA = "Área (nombre)"
LBL_CARGO = "Cargo"
LBL_CLAS = "Clasificación"
LBL_TS = "Trabajadora Social"
LBL_EMP = "Empresa"
LBL_NAC = "Nacionalidad"
LBL_LUG = "Lugar Registro"
LBL_REG = "Región Registro"
LBL_TENURE_BUCKET = "Antigüedad (bucket)"
LBL_AGE_BUCKET = "Edad (bucket)"

# Opciones
LBL_OPT_UNIQUE_DAY = "Salidas: contar personas únicas por día"
LBL_OPT_SHOW_LABELS = "Mostrar etiquetas de datos"
LBL_OPT_TOPN = "Top N categorías (barras/pastel)"
LBL_OPT_DESC_VARS = "Variables descriptivas (dinámico)"
LBL_OPT_DESC_DATASET = "Dataset descriptivo"
LBL_OPT_DESC_DATASET_1 = "Existencias (snapshot)"
LBL_OPT_DESC_DATASET_2 = "Salidas (en rango)"
LBL_OPT_DESC_VAR_PICK = "Variable a describir"

# Mensajes
MSG_NEED_DATA = "Carga datos y define rango/filtros para ver el panel."
MSG_LOAD_FILE_TO_START = "Carga un archivo para iniciar."
MSG_PATH_NOT_FOUND = "La ruta no existe."
MSG_READ_FAIL = "No se pudo leer el archivo:"
MSG_NO_DATA_FOR_VIEW = "No hay datos suficientes con los filtros actuales."


# =============================================================================
# Config Streamlit
# =============================================================================
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)


# =============================================================================
# Columnas esperadas (Historia Personal)
# - %R es opcional (si no está, se asume 1.0)
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

# Referencias
AREA_REF: Dict[str, Tuple[str, str]] = {
    "ADM": ("ADMINISTRACIÓN", "ADMINISTRACIÓN"),
    "COMPRAS": ("COMPRAS", "ADMINISTRACIÓN"),
    "CONTA": ("CONTABILIDAD", "ADMINISTRACIÓN"),
    "FIN": ("FINANZAS", "ADMINISTRACIÓN"),
    "ING": ("INGENIERÍA", "ADMINISTRACIÓN"),
    "DISTRIBUCION": ("DISTRIBUCIÓN Y TRÁFICO", "ADMINISTRACIÓN"),
    "PROD": ("PRODUCCIÓN", "ADMINISTRACIÓN"),
    "SSO": ("SEGURIDAD Y SALUD OCUPACIONAL", "ADMINISTRACIÓN"),
    "TTHH": ("TALENTO HUMANO", "ADMINISTRACIÓN"),
    "SISTE": ("SISTEMAS", "ADMINISTRACIÓN"),
    "VENT": ("VENTAS", "ADMINISTRACIÓN"),

    "LAB": ("LABORATORIO", "PRODUCCIÓN – PROPAGACIÓN"),
    "A-4": ("SAN JUAN", "PRODUCCIÓN – CAMPO"),
    "CULTIVOS VARIOS": ("CULTIVOS VARIOS", "PRODUCCIÓN – CAMPO"),
    "MH1": ("MONJASHUAICO 1", "PRODUCCIÓN – CAMPO"),
    "MH2": ("MONJASHUAICO 2", "PRODUCCIÓN – CAMPO"),
    "RIEGO": ("RIEGO", "PRODUCCIÓN – CAMPO"),
    "ORN": ("ORNAMENTALES", "PRODUCCIÓN – ORNAMENTALES"),

    "CLS": ("CLASIFICACIÓN", "PRODUCCIÓN – POSCOSECHA"),
    "EMP": ("EMPAQUE", "PRODUCCIÓN – POSCOSECHA"),
    "SB": ("SALA DE BROTE", "PRODUCCIÓN – POSCOSECHA"),

    "PROP": ("PROPAGACIÓN", "PRODUCCIÓN – PROPAGACIÓN"),

    "MANT": ("MANTENIMIENTO", "PRODUCCIÓN – TRANSVERSAL"),
    "BOD": ("BODEGA", "PRODUCCIÓN – TRANSVERSAL"),
    "DRONES": ("OPERACIÓN DE DRONES", "PRODUCCIÓN – TRANSVERSAL"),
    "MONITOREO": ("MONITOREO", "PRODUCCIÓN – TRANSVERSAL"),

    "CHOFER": ("TRANSPORTE INTERNO", "SERVICIOS GENERALES"),
    "SP": ("SERVICIOS PRESTADOS", "SERVICIOS GENERALES"),
    "SRG": ("SRG (SERVICIOS GENERALES)", "SERVICIOS GENERALES"),
    "џPAS": ("PASANTÍA", "SERVICIOS GENERALES"),
    "PAS": ("PASANTÍA", "SERVICIOS GENERALES"),
    "PRACT": ("PRACTICANTES", "SERVICIOS GENERALES"),
}

CLAS_REF: Dict[str, str] = {
    "ADM": "ADMINISTRATIVO",
    "AGR": "TRABAJADOR AGRÍCOLA",
    "CHOFER": "CHOFER",
    "OCAS": "TRABAJADOR AGRÍCOLA OCASIONAL",
    "PAS": "PASANTÍA",
    "PRACT": "PRACTICANTES",
    "SP": "SERVICIOS PRESTADOS",
}


# =============================================================================
# Helpers
# =============================================================================
def _to_datetime(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.normalize()

def today_dt() -> pd.Timestamp:
    return pd.Timestamp(date.today())

def excel_weeknum_return_type_1(d: pd.Series) -> pd.Series:
    # Excel WEEKNUM(date,1): weeks start Sunday
    return d.dt.strftime("%U").astype(int) + 1

def week_end_sun_to_sat(d: pd.Series) -> pd.Series:
    wd = d.dt.weekday  # Mon=0..Sun=6
    days_since_sun = (wd + 1) % 7
    wstart = d - pd.to_timedelta(days_since_sun, unit="D")
    return (wstart + pd.to_timedelta(6, unit="D")).dt.normalize()

def month_end(d: pd.Series) -> pd.Series:
    return (d + pd.offsets.MonthEnd(0)).dt.normalize()

def add_calendar_fields(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    out = df.copy()
    d = pd.to_datetime(out[date_col], errors="coerce").dt.normalize()

    out["Día"] = d
    out["Año"] = d.dt.year.astype("int64")
    out["Mes"] = d.dt.month.astype("int64")
    out["Semana"] = excel_weeknum_return_type_1(d).astype("int64")

    yy = (out["Año"] % 100).astype(int).astype(str).str.zfill(2)
    ww = out["Semana"].astype(int).astype(str).str.zfill(2)
    mm = out["Mes"].astype(int).astype(str).str.zfill(2)

    out["CodSem"] = (yy + ww).astype(str)  # YYWW
    out["CodMes"] = (yy + mm).astype(str)  # YYMM

    out["FinSemana"] = week_end_sun_to_sat(d)
    out["FinMes"] = month_end(d)
    return out

def _years_offset_date(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + years)

def _safe_table_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c) for c in out.columns]
    return out

def fmt_es(x: float, dec: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_int_es(x: float) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{int(round(x)):,}".replace(",", ".")

def apply_bar_labels(fig, show_labels: bool, orientation: str = "v") -> go.Figure:
    if not show_labels:
        return fig
    if orientation == "h":
        fig.update_traces(
            texttemplate="%{x:.0f}",
            textposition="outside",
            cliponaxis=False,
        )
    else:
        fig.update_traces(
            texttemplate="%{y:.0f}",
            textposition="outside",
            cliponaxis=False,
        )
    return fig

def apply_line_labels(fig: go.Figure, show_labels: bool) -> go.Figure:
    if not show_labels:
        return fig
    # Para que no sea un “chorizo”, etiqueta solo el último punto de cada serie
    for tr in fig.data:
        if getattr(tr, "mode", "") and "lines" in tr.mode:
            x = tr.x
            y = tr.y
            if x is not None and y is not None and len(x) > 0:
                last_x = [x[-1]]
                last_y = [y[-1]]
                fig.add_trace(
                    go.Scatter(
                        x=last_x,
                        y=last_y,
                        mode="markers+text",
                        text=[fmt_es(float(last_y[0]), 3) if (last_y[0] is not None and not pd.isna(last_y[0])) else "-"],
                        textposition="top right",
                        showlegend=False,
                    )
                )
    return fig

def nice_xaxis(fig):
    fig.update_xaxes(type="category", automargin=True)
    fig.update_layout(margin=dict(b=70))
    return fig


# =============================================================================
# Mapping Área y Clasificación
# =============================================================================
def _map_area(area_raw: pd.Series) -> Tuple[pd.Series, pd.Series]:
    key = area_raw.astype("string").str.strip()
    key_u = key.str.upper()

    std = key_u.map(lambda x: AREA_REF.get(x, (None, None))[0] if pd.notna(x) else None)
    gen = key_u.map(lambda x: AREA_REF.get(x, (None, None))[1] if pd.notna(x) else None)

    std = std.fillna(key).replace({"": pd.NA}).fillna(MISSING_LABEL).astype("string")
    gen = gen.fillna(pd.NA).replace({"": pd.NA}).fillna(MISSING_LABEL).astype("string")
    return std, gen

def _map_clas(clas_raw: pd.Series) -> pd.Series:
    key = clas_raw.astype("string").str.strip()
    key_u = key.str.upper()
    std = key_u.map(lambda x: CLAS_REF.get(x, None) if pd.notna(x) else None)
    std = std.fillna(key).replace({"": pd.NA}).fillna(MISSING_LABEL).astype("string")
    return std


# =============================================================================
# Lectura robusta
# =============================================================================
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


# =============================================================================
# Preparación de Historia Personal
# =============================================================================
KEEP_INTERNAL = [
    "cod", "ini", "fin", "fin_eff", "fnac",
    "r_pct",
    "clas_raw", "clas",
    "sexo", "ts", "emp",
    "area_raw", "area", "area_gen",
    "cargo", "nac", "lug", "reg",
]

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

    out["ini"] = _to_datetime(out["ini"])
    out["fin"] = _to_datetime(out["fin"])
    out["fnac"] = _to_datetime(out["fnac"])
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

    out["area"], out["area_gen"] = _map_area(out["area_raw"])
    out["clas"] = _map_clas(out["clas_raw"])

    out = out[KEEP_INTERNAL].copy()
    out = out.sort_values(["cod", "ini", "fin_eff"]).reset_index(drop=True)
    return out


# =============================================================================
# Intervalos por persona (para existencias diarias)
# =============================================================================
@st.cache_data(show_spinner=False)
def merge_intervals_per_person(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
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


# =============================================================================
# Buckets
# =============================================================================
TENURE_BUCKETS = {
    "< 30 días": (0, 29),
    "30 - 90 días": (30, 90),
    "91 - 180 días": (91, 180),
    "181 - 360 días": (181, 360),
    "> 360 días": (361, None),
}

AGE_BUCKETS = {
    "< 24 años": (None, 23),
    "24 - 30 años": (24, 30),
    "31 - 37 años": (31, 37),
    "38 - 42 años": (38, 42),
    "43 - 49 años": (43, 49),
    "50 - 56 años": (50, 56),
    "> 56 años": (57, None),
}

def bucket_antiguedad(days: pd.Series) -> pd.Series:
    d = days.astype("float")
    out = pd.Series(np.where(d.isna(), MISSING_LABEL, ""), index=days.index, dtype="object")
    out = np.where((~pd.isna(d)) & (d >= 0) & (d < 30), "< 30 días", out)
    out = np.where((~pd.isna(d)) & (d >= 30) & (d <= 90), "30 - 90 días", out)
    out = np.where((~pd.isna(d)) & (d >= 91) & (d <= 180), "91 - 180 días", out)
    out = np.where((~pd.isna(d)) & (d >= 181) & (d <= 360), "181 - 360 días", out)
    out = np.where((~pd.isna(d)) & (d >= 361), "> 360 días", out)
    return pd.Series(out, index=days.index, dtype="object")

def bucket_edad_from_dob(dob: pd.Series, ref: pd.Series) -> pd.Series:
    out = pd.Series(MISSING_LABEL, index=dob.index, dtype="object")
    mask = (~dob.isna()) & (~ref.isna())
    if not mask.any():
        return out

    dob2 = dob[mask]
    ref2 = ref[mask]

    had_bday = (ref2.dt.month > dob2.dt.month) | ((ref2.dt.month == dob2.dt.month) & (ref2.dt.day >= dob2.dt.day))
    edad = (ref2.dt.year - dob2.dt.year) - (~had_bday).astype(int)

    out.loc[mask] = np.where(edad < 24, "< 24 años", out.loc[mask])
    out.loc[mask] = np.where((edad >= 24) & (edad <= 30), "24 - 30 años", out.loc[mask])
    out.loc[mask] = np.where((edad >= 31) & (edad <= 37), "31 - 37 años", out.loc[mask])
    out.loc[mask] = np.where((edad >= 38) & (edad <= 42), "38 - 42 años", out.loc[mask])
    out.loc[mask] = np.where((edad >= 43) & (edad <= 49), "43 - 49 años", out.loc[mask])
    out.loc[mask] = np.where((edad >= 50) & (edad <= 56), "50 - 56 años", out.loc[mask])
    out.loc[mask] = np.where((edad >= 57), "> 56 años", out.loc[mask])
    return out


# =============================================================================
# Filtros
# =============================================================================
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

def apply_categorical_filters(df: pd.DataFrame, fs: FilterState) -> pd.DataFrame:
    out = df.copy()

    def _apply(col: str, selected: List[str]) -> None:
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


# =============================================================================
# Ventanas por periodo
# =============================================================================
def build_period_windows(start: pd.Timestamp, end: pd.Timestamp, period: str) -> pd.DataFrame:
    days = pd.date_range(start, end, freq="D")
    cal = add_calendar_fields(pd.DataFrame({"Día": days}), "Día")

    if period == "D":
        w = cal[["Día"]].copy()
        w["window_start"] = w["Día"]
        w["window_end"] = w["Día"]
        w["cut"] = w["Día"]
        w["Periodo"] = w["Día"].dt.strftime("%Y-%m-%d")
        return w[["Periodo", "cut", "window_start", "window_end"]]

    if period == "W":
        w = cal.groupby("CodSem", as_index=False).agg(
            window_start=("Día", "min"),
            window_end=("Día", "max"),
            cut=("FinSemana", "max"),
        )
        w["Periodo"] = w["CodSem"].astype(str)
        return w[["Periodo", "cut", "window_start", "window_end"]].sort_values("cut")

    if period == "M":
        w = cal.groupby("CodMes", as_index=False).agg(
            window_start=("Día", "min"),
            window_end=("Día", "max"),
            cut=("FinMes", "max"),
        )
        w["Periodo"] = w["CodMes"].astype(str)
        return w[["Periodo", "cut", "window_start", "window_end"]].sort_values("cut")

    if period == "Y":
        w = cal.groupby("Año", as_index=False).agg(
            window_start=("Día", "min"),
            window_end=("Día", "max"),
            cut=("Día", "max"),
        )
        w["Periodo"] = w["Año"].astype(int).astype(str)
        return w[["Periodo", "cut", "window_start", "window_end"]].sort_values("cut")

    raise ValueError("period inválido")


# =============================================================================
# Existencias y Salidas (diario)
# =============================================================================
@st.cache_data(show_spinner=False)
def compute_existencias_daily_filtered_fast(
    df_intervals: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    antig_sel: List[str],
    edad_sel: List[str],
) -> pd.DataFrame:
    idx = pd.date_range(start, end, freq="D")
    n = len(idx)
    if n == 0:
        return pd.DataFrame({"Día": [], "Existencias": []})

    g = df_intervals[(df_intervals["ini"] <= end) & (df_intervals["fin_eff"] >= start)].copy()
    if g.empty:
        out = pd.DataFrame({"Día": idx, "Existencias": np.zeros(n, dtype=int)})
        return add_calendar_fields(out, "Día")

    use_antig = bool(antig_sel)
    use_edad = bool(edad_sel)

    ini_days = g["ini"].values.astype("datetime64[D]").astype("int64")
    fin_days = g["fin_eff"].values.astype("datetime64[D]").astype("int64")
    start_day = np.datetime64(start, "D").astype("int64")
    end_day = np.datetime64(end, "D").astype("int64")

    diff = np.zeros(n + 1, dtype=np.int64)

    antig_list = [b for b in antig_sel if b in TENURE_BUCKETS] if use_antig else []
    edad_list = [b for b in edad_sel if b in AGE_BUCKETS] if use_edad else []
    edad_allow_sindato = use_edad and (MISSING_LABEL in edad_sel)

    fnac_vals = g["fnac"].values

    for i in range(len(g)):
        base_s = max(ini_days[i], start_day)
        base_e = min(fin_days[i], end_day)
        if base_s > base_e:
            continue

        if (not use_antig) and (not use_edad):
            s_idx = int(base_s - start_day)
            e_idx = int(base_e - start_day)
            diff[s_idx] += 1
            diff[e_idx + 1 if (e_idx + 1 < n) else n] -= 1
            continue

        dob_ts = fnac_vals[i]
        dob_missing = pd.isna(dob_ts)
        if use_edad and dob_missing and not edad_allow_sindato:
            continue

        ini0 = ini_days[i]

        # Antig
        if use_antig and antig_list:
            antig_ranges = []
            for b in antig_list:
                a0, a1 = TENURE_BUCKETS[b]
                s = max(ini0 + a0, base_s)
                e = min(base_e, (base_e if a1 is None else ini0 + a1))
                if s <= e:
                    antig_ranges.append((s, e))
            if not antig_ranges:
                continue
        else:
            antig_ranges = [(base_s, base_e)]

        # Edad
        if use_edad and (not dob_missing) and edad_list:
            dob_date = pd.Timestamp(dob_ts).date()
            edad_ranges = []
            for b in edad_list:
                y0, y1 = AGE_BUCKETS[b]
                s_date = start.date() if y0 is None else _years_offset_date(dob_date, y0)
                e_date = end.date() if y1 is None else (_years_offset_date(dob_date, y1 + 1) - timedelta(days=1))

                s = max(np.int64(np.datetime64(s_date, "D").astype("int64")), base_s)
                e = min(np.int64(np.datetime64(e_date, "D").astype("int64")), base_e)
                if s <= e:
                    edad_ranges.append((s, e))
            if not edad_ranges:
                continue
        else:
            edad_ranges = [(base_s, base_e)]

        # Intersección
        for (as_, ae_) in antig_ranges:
            for (es_, ee_) in edad_ranges:
                s = max(as_, es_)
                e = min(ae_, ee_)
                if s <= e:
                    s_idx = int(s - start_day)
                    e_idx = int(e - start_day)
                    diff[s_idx] += 1
                    diff[e_idx + 1 if (e_idx + 1 < n) else n] -= 1

    exist = np.cumsum(diff[:-1]).astype(int)
    out = pd.DataFrame({"Día": idx, "Existencias": exist})
    return add_calendar_fields(out, "Día")


@st.cache_data(show_spinner=False)
def compute_salidas_daily_filtered(
    df_events: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    antig_sel: List[str],
    edad_sel: List[str],
    unique_personas_por_dia: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    idx = pd.date_range(start, end, freq="D")
    if len(idx) == 0:
        return pd.DataFrame({"Día": [], "Salidas": []}), df_events.iloc[0:0].copy()

    d = df_events[~df_events["fin"].isna()].copy()
    d = d[(d["fin"] >= start) & (d["fin"] <= end)].copy()

    if d.empty:
        out = pd.DataFrame({"Día": idx, "Salidas": np.zeros(len(idx), dtype=int)})
        return add_calendar_fields(out, "Día"), d

    d = d.rename(columns={"fin": "ref_fin"})
    d["ref_fin"] = _to_datetime(d["ref_fin"])

    d["antig_dias"] = (d["ref_fin"] - d["ini"]).dt.days
    d["Antigüedad"] = bucket_antiguedad(d["antig_dias"])
    d["Edad"] = bucket_edad_from_dob(d["fnac"], d["ref_fin"])

    if antig_sel:
        d = d[d["Antigüedad"].isin(antig_sel)]
    if edad_sel:
        d = d[d["Edad"].isin(edad_sel)]

    if unique_personas_por_dia:
        g = d.groupby("ref_fin")["cod"].nunique().rename("Salidas")
    else:
        g = d.groupby("ref_fin")["cod"].size().rename("Salidas")

    out = pd.DataFrame({"Día": idx}).merge(
        g.reset_index().rename(columns={"ref_fin": "Día"}),
        on="Día",
        how="left",
    )
    out["Salidas"] = out["Salidas"].fillna(0).astype(int)
    out = add_calendar_fields(out, "Día")
    return out, d


# =============================================================================
# Agregación a periodo (simple y claro)
# =============================================================================
@st.cache_data(show_spinner=False)
def aggregate_daily_to_period_simple(df_daily: pd.DataFrame, period: str) -> pd.DataFrame:
    d = df_daily.copy()
    if "CodSem" not in d.columns or "CodMes" not in d.columns or "Año" not in d.columns:
        d = add_calendar_fields(d, "Día")

    key = {"D": "Día", "W": "CodSem", "M": "CodMes", "Y": "Año"}[period]
    cut_col = {"D": "Día", "W": "FinSemana", "M": "FinMes", "Y": "Día"}[period]

    def _agg(g: pd.DataFrame) -> pd.Series:
        ws = g["Día"].min()
        we = g["Día"].max()
        cut = g[cut_col].max() if cut_col in g.columns else we
        sal = float(np.nansum(g["Salidas"].astype(float).values)) if "Salidas" in g.columns else 0.0
        exist_prom = float(np.nanmean(g["Existencias"].astype(float).values)) if "Existencias" in g.columns else np.nan
        return pd.Series({
            "window_start": ws,
            "window_end": we,
            "cut": cut,
            "Salidas": sal,
            "Existencias_Prom": exist_prom,
        })

    out = d.groupby(key, dropna=False, as_index=False).apply(_agg).reset_index(drop=True)

    if period == "D":
        out["Periodo"] = pd.to_datetime(out["window_start"]).dt.strftime("%Y-%m-%d")
    elif period in ("W", "M"):
        out["Periodo"] = out[key].astype(str)
    else:
        out["Periodo"] = out[key].astype(int).astype(str)

    out = out.sort_values("cut").reset_index(drop=True)
    return out[["Periodo", "cut", "window_start", "window_end", "Salidas", "Existencias_Prom"]]


# =============================================================================
# Métrica pedida: 1 - Supervivencia a 30 días (proporción simple)
# - Cohorte por periodo: spells con ini dentro de la ventana y con follow-up completo (ini <= cut_today - 30)
# =============================================================================
@st.cache_data(show_spinner=False)
def compute_desercion30_by_period(
    df_events: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    period: str,
    cut_today: pd.Timestamp,
    H_days: int = 30,
) -> pd.DataFrame:
    if df_events.empty:
        return pd.DataFrame()

    windows = build_period_windows(start, end, period).copy()
    if windows.empty:
        return pd.DataFrame()

    ct = pd.Timestamp(cut_today).normalize()
    H = int(H_days)

    rows = []
    for _, w in windows.iterrows():
        ws = pd.Timestamp(w["window_start"]).normalize()
        we = pd.Timestamp(w["window_end"]).normalize()

        cohort = df_events[(df_events["ini"] >= ws) & (df_events["ini"] <= we)].copy()
        if cohort.empty:
            rows.append({
                "Periodo": w["Periodo"],
                "cut": w["cut"],
                "cohort_n": 0,
                "surv30": np.nan,
                "kpi_desercion30": np.nan,
            })
            continue

        # follow-up completo
        cohort = cohort[cohort["ini"] <= (ct - pd.Timedelta(days=H))].copy()
        n = int(len(cohort))
        if n <= 0:
            rows.append({
                "Periodo": w["Periodo"],
                "cut": w["cut"],
                "cohort_n": 0,
                "surv30": np.nan,
                "kpi_desercion30": np.nan,
            })
            continue

        # sobrevivió si sigue activo al día ini+H (fin_eff >= ini+H)
        survived = (cohort["fin_eff"] >= (cohort["ini"] + pd.Timedelta(days=H))).sum()
        surv = float(survived) / float(n) if n > 0 else np.nan
        kpi = 1.0 - surv if pd.notna(surv) else np.nan

        rows.append({
            "Periodo": w["Periodo"],
            "cut": w["cut"],
            "cohort_n": n,
            "surv30": surv,
            "kpi_desercion30": kpi,
        })

    out = pd.DataFrame(rows).sort_values("cut").reset_index(drop=True)
    return out


def meta_from_last_year_last3(df_metric: pd.DataFrame, end_dt: pd.Timestamp, value_col: str) -> float:
    if df_metric is None or df_metric.empty or value_col not in df_metric.columns:
        return np.nan
    last_year = int(pd.Timestamp(end_dt).year) - 1
    d = df_metric.copy()
    d["cut"] = pd.to_datetime(d["cut"], errors="coerce")
    d = d[d["cut"].dt.year == last_year].copy()
    d = d.dropna(subset=[value_col]).sort_values("cut")
    if d.empty:
        return np.nan
    tail = d[value_col].tail(3)
    if tail.empty:
        return np.nan
    return float(np.nanmean(tail.values))


# =============================================================================
# Descriptivos: topN + OTROS + gráfico barras/pastel
# =============================================================================
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


def bar_and_pie(df_counts: pd.DataFrame, title: str, show_labels: bool, topn: int) -> Tuple[go.Figure, go.Figure]:
    # Barra horizontal
    d = df_counts.copy()
    d = d.sort_values("N", ascending=True)
    figb = px.bar(d, x="N", y="Categoria", orientation="h", title=title)
    figb = apply_bar_labels(figb, show_labels, orientation="h")

    # Pastel
    figp = px.pie(df_counts, names="Categoria", values="N", title=title)
    figp.update_traces(textinfo="label+percent" if show_labels else "percent")
    return figb, figp


# =============================================================================
# UI superior
# =============================================================================
top = st.container()
with top:
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        show_filters = st.toggle(LBL_SHOW_FILTERS, value=True)
    with c2:
        view = st.radio(LBL_VIEW_PICK, options=[VIEW_1, VIEW_2], horizontal=True, index=0)

if show_filters:
    col_filters, col_main = st.columns([1, 3], gap="large")
else:
    col_filters = None
    col_main = st.container()


# =============================================================================
# Panel de control
# =============================================================================
if show_filters:
    with col_filters:
        st.subheader(PANEL_TITLE)
        tab_p, tab_f, tab_o = st.tabs([TAB_DATA, TAB_FILTERS, TAB_OPTIONS])

        # -------------------------
        # TAB: Datos & Periodo
        # -------------------------
        with tab_p:
            uploaded = st.file_uploader(LBL_UPLOAD_MAIN, type=["xlsx", "xls", "csv"], key="uploader_hist")
            path = st.text_input(LBL_PATH_MAIN, value="", key="path_hist")

            df_raw = None
            sheet_hist = None

            if uploaded is None and not path.strip():
                st.info(MSG_LOAD_FILE_TO_START)
                st.stop()

            try:
                if uploaded is not None:
                    if uploaded.name.lower().endswith(".csv"):
                        df_raw = read_csv_any(uploaded)
                    else:
                        xls = pd.ExcelFile(uploaded)
                        sheet_hist = st.selectbox(LBL_SHEET_MAIN, options=xls.sheet_names, index=0, key="sheet_hist_upload")
                        df_raw = read_excel_strict_hist(uploaded, sheet_hist)
                else:
                    p = path.strip()
                    if not os.path.exists(p):
                        st.error(MSG_PATH_NOT_FOUND)
                        st.stop()
                    if p.lower().endswith(".csv"):
                        df_raw = read_csv_any(p)
                    else:
                        xls = pd.ExcelFile(p)
                        sheet_hist = st.selectbox(LBL_SHEET_MAIN, options=xls.sheet_names, index=0, key="sheet_hist_path")
                        df_raw = read_excel_strict_hist(p, sheet_hist)

            except Exception as e:
                st.error(f"{MSG_READ_FAIL} {e}")
                st.stop()

            try:
                df0 = validate_and_prepare_hist(df_raw)
            except Exception as e:
                st.error(str(e))
                st.stop()

            df_intervals_all = merge_intervals_per_person(df0)

            min_date = df_intervals_all["ini"].min()
            max_date = df_intervals_all["fin_eff"].max()
            default_end = min(today_dt(), max_date) if pd.notna(max_date) else today_dt()
            default_start = max(min_date, default_end - pd.Timedelta(days=180)) if pd.notna(min_date) else (default_end - pd.Timedelta(days=180))

            preset = st.selectbox(
                LBL_RANGE_PRESET,
                options=["Personalizado", "Últimos 30 días", "Últimos 90 días", "Últimos 180 días", "Últimos 365 días", "Año actual (YTD)"],
                index=2,
                key="range_preset",
            )

            if "date_range_main" not in st.session_state:
                st.session_state["date_range_main"] = (default_start.date(), default_end.date())

            if preset != "Personalizado":
                end_p = default_end.date()
                if preset == "Últimos 30 días":
                    start_p = (default_end - pd.Timedelta(days=30)).date()
                elif preset == "Últimos 90 días":
                    start_p = (default_end - pd.Timedelta(days=90)).date()
                elif preset == "Últimos 180 días":
                    start_p = (default_end - pd.Timedelta(days=180)).date()
                elif preset == "Últimos 365 días":
                    start_p = (default_end - pd.Timedelta(days=365)).date()
                else:
                    start_p = date(default_end.year, 1, 1)

                if pd.notna(min_date):
                    start_p = max(start_p, min_date.date())
                if pd.notna(max_date):
                    end_p = min(end_p, max_date.date())

                st.session_state["date_range_main"] = (start_p, end_p)

            r0, r1 = st.slider(
                LBL_RANGE_SLIDER,
                min_value=(min_date.date() if pd.notna(min_date) else date(2000, 1, 1)),
                max_value=(max_date.date() if pd.notna(max_date) else default_end.date()),
                value=st.session_state["date_range_main"],
                key="date_range_slider",
            )
            st.session_state["date_range_main"] = (r0, r1)

            start_dt = pd.Timestamp(st.session_state["date_range_main"][0])
            end_dt = pd.Timestamp(st.session_state["date_range_main"][1])
            if start_dt > end_dt:
                st.error("Inicio > Fin.")
                st.stop()

            period_label = st.selectbox(LBL_GROUP_BY, options=["Día", "Semana", "Mes", "Año"], index=1, key="period_group")
            period = {"Día": "D", "Semana": "W", "Mes": "M", "Año": "Y"}[period_label]

            snap_date = st.slider(
                LBL_SNAPSHOT_DATE,
                min_value=start_dt.date(),
                max_value=end_dt.date(),
                value=end_dt.date(),
                key="snap_date",
            )
            snap_dt = pd.Timestamp(snap_date)

            cut_today = min(today_dt(), max_date) if pd.notna(max_date) else today_dt()
            st.write(f"{LBL_TODAY_CUT}: **{cut_today.date()}**")

            st.session_state["__globals__"] = {
                "df0": df0,
                "df_intervals_all": df_intervals_all,
                "start_dt": start_dt,
                "end_dt": end_dt,
                "period": period,
                "period_label": period_label,
                "snap_dt": snap_dt,
                "cut_today": cut_today,
            }

        # -------------------------
        # TAB: Filtros
        # -------------------------
        with tab_f:
            g = st.session_state.get("__globals__")
            if not g:
                st.stop()
            df0 = g["df0"]

            st.caption(LBL_FILTERS_HINT)

            def opts(df: pd.DataFrame, col: str) -> List[str]:
                v = df[col].dropna().astype(str).str.strip()
                v = v[v != ""].unique().tolist()
                return sorted(v)

            if st.button(BTN_CLEAR_FILTERS, use_container_width=True, key="btn_clear_filters"):
                for k in [
                    "f_sexo", "f_area_gen", "f_area", "f_cargo", "f_clas", "f_ts", "f_emp",
                    "f_nac", "f_lug", "f_reg", "f_antig", "f_edad",
                ]:
                    st.session_state[k] = []
                st.rerun()

            area_gen_pick = st.multiselect(LBL_AREA_GEN, opts(df0, "area_gen"), default=st.session_state.get("f_area_gen", []), key="f_area_gen")

            if area_gen_pick:
                df_area = df0[df0["area_gen"].isin(area_gen_pick)]
                area_opts = opts(df_area, "area")
            else:
                area_opts = opts(df0, "area")

            fs = FilterState(
                sexo=st.multiselect(LBL_SEXO, opts(df0, "sexo"), default=st.session_state.get("f_sexo", []), key="f_sexo"),
                area_gen=area_gen_pick,
                area=st.multiselect(LBL_AREA, area_opts, default=st.session_state.get("f_area", []), key="f_area"),
                cargo=st.multiselect(LBL_CARGO, opts(df0, "cargo"), default=st.session_state.get("f_cargo", []), key="f_cargo"),
                clas=st.multiselect(LBL_CLAS, opts(df0, "clas"), default=st.session_state.get("f_clas", []), key="f_clas"),
                ts=st.multiselect(LBL_TS, opts(df0, "ts"), default=st.session_state.get("f_ts", []), key="f_ts"),
                emp=st.multiselect(LBL_EMP, opts(df0, "emp"), default=st.session_state.get("f_emp", []), key="f_emp"),
                nac=st.multiselect(LBL_NAC, opts(df0, "nac"), default=st.session_state.get("f_nac", []), key="f_nac"),
                lug=st.multiselect(LBL_LUG, opts(df0, "lug"), default=st.session_state.get("f_lug", []), key="f_lug"),
                reg=st.multiselect(LBL_REG, opts(df0, "reg"), default=st.session_state.get("f_reg", []), key="f_reg"),
                antig=st.multiselect(
                    LBL_TENURE_BUCKET,
                    list(TENURE_BUCKETS.keys()) + [MISSING_LABEL],
                    default=st.session_state.get("f_antig", []),
                    key="f_antig",
                ),
                edad=st.multiselect(
                    LBL_AGE_BUCKET,
                    list(AGE_BUCKETS.keys()) + [MISSING_LABEL],
                    default=st.session_state.get("f_edad", []),
                    key="f_edad",
                ),
            )
            st.session_state["__fs__"] = fs

        # -------------------------
        # TAB: Opciones
        # -------------------------
        with tab_o:
            unique_personas_por_dia = st.checkbox(LBL_OPT_UNIQUE_DAY, value=True, key="opt_unique_day")
            show_labels = st.checkbox(LBL_OPT_SHOW_LABELS, value=True, key="opt_show_labels")
            topn = int(st.number_input(LBL_OPT_TOPN, min_value=5, max_value=30, value=10, step=1, key="opt_topn"))

            # Variables descriptivas (dinámico)
            desc_vars_catalog = {
                "Área General": "area_gen",
                "Área": "area",
                "Cargo": "cargo",
                "Clasificación": "clas",
                "Sexo": "sexo",
                "TS": "ts",
                "Empresa": "emp",
                "Nacionalidad": "nac",
                "Lugar Registro": "lug",
                "Región Registro": "reg",
                "Antigüedad (bucket)": "Antigüedad",
                "Edad (bucket)": "Edad",
            }
            default_desc = ["Área General", "Área", "Clasificación"]
            desc_vars = st.multiselect(
                LBL_OPT_DESC_VARS,
                list(desc_vars_catalog.keys()),
                default=st.session_state.get("opt_desc_vars", default_desc),
                key="opt_desc_vars",
            )

            st.session_state["__opts__"] = {
                "unique_personas_por_dia": unique_personas_por_dia,
                "show_labels": show_labels,
                "topn": topn,
                "desc_vars": desc_vars,
                "desc_vars_catalog": desc_vars_catalog,
            }


# =============================================================================
# MAIN
# =============================================================================
with (col_main if hasattr(col_main, "__enter__") else st.container()):
    g = st.session_state.get("__globals__")
    fs = st.session_state.get("__fs__")
    opts = st.session_state.get("__opts__")

    if not g or not fs or not opts:
        st.warning(MSG_NEED_DATA if not show_filters else MSG_LOAD_FILE_TO_START)
        st.stop()

    df0 = g["df0"]
    df_intervals_all = g["df_intervals_all"]
    start_dt = g["start_dt"]
    end_dt = g["end_dt"]
    period = g["period"]
    period_label = g["period_label"]
    snap_dt = g["snap_dt"]
    cut_today = g["cut_today"]

    unique_personas_por_dia = bool(opts["unique_personas_por_dia"])
    show_labels = bool(opts["show_labels"])
    topn = int(opts["topn"])
    desc_vars = list(opts["desc_vars"])
    desc_vars_catalog = dict(opts["desc_vars_catalog"])

    # 1) Filtros categóricos
    df0_f = apply_categorical_filters(df0, fs)
    if df0_f.empty:
        st.warning(MSG_NO_DATA_FOR_VIEW)
        st.stop()

    # 2) Series diarias Existencias/Salidas (con buckets de edad/antig)
    with st.spinner("Calculando existencias y salidas..."):
        df_intervals_f = merge_intervals_per_person(df0_f)

        df_sal_daily, df_sal_det = compute_salidas_daily_filtered(
            df_events=df0_f,
            start=start_dt,
            end=end_dt,
            antig_sel=fs.antig,
            edad_sel=fs.edad,
            unique_personas_por_dia=unique_personas_por_dia,
        )
        df_exist_daily = compute_existencias_daily_filtered_fast(
            df_intervals=df_intervals_f,
            start=start_dt,
            end=end_dt,
            antig_sel=fs.antig,
            edad_sel=fs.edad,
        )

        df_daily = df_sal_daily.merge(df_exist_daily[["Día", "Existencias"]], on="Día", how="left")
        df_daily["Existencias"] = df_daily["Existencias"].fillna(0).astype(int)
        df_daily = add_calendar_fields(df_daily, "Día")

        df_period = aggregate_daily_to_period_simple(df_daily, period)

    # 3) KPI: 1 - supervivencia 30 días (por periodo) + MA3 (rango actual)
    H_DAYS = 30
    with st.spinner("Calculando (1 - supervivencia 30 días) + meta..."):
        kpi_period = compute_desercion30_by_period(
            df_events=df0_f,
            start=start_dt,
            end=end_dt,
            period=period,
            cut_today=cut_today,
            H_days=H_DAYS,
        )

        # MA3 (solo para suavizar la serie visible)
        kpi_period = kpi_period.sort_values("cut").reset_index(drop=True)
        kpi_period["MA3"] = kpi_period["kpi_desercion30"].rolling(window=3, min_periods=1).mean()

        # Meta = promedio de los últimos 3 registros del AÑO PASADO (baseline = sin filtros)
        last_year = int(end_dt.year) - 1
        base_start = pd.Timestamp(date(last_year, 1, 1))
        base_end = pd.Timestamp(date(last_year, 12, 31))

        kpi_base = compute_desercion30_by_period(
            df_events=df0,               # baseline SIN filtros
            start=base_start,
            end=base_end,
            period=period,
            cut_today=cut_today,
            H_days=H_DAYS,
        )
        meta_val = meta_from_last_year_last3(kpi_base, end_dt=end_dt, value_col="kpi_desercion30")
        kpi_period["Meta"] = meta_val

    # =============================================================================
    # VIEW 1: DASHBOARD
    # =============================================================================
    if view == VIEW_1:
        st.subheader("Dashboard")

        # KPIs arriba
        total_salidas = float(df_period["Salidas"].sum()) if not df_period.empty else 0.0
        exist_prom_rango = float(np.nanmean(df_period["Existencias_Prom"].values)) if not df_period.empty else np.nan

        kpi_last = kpi_period.dropna(subset=["kpi_desercion30"]).tail(1)
        last_kpi = float(kpi_last["kpi_desercion30"].iloc[0]) if not kpi_last.empty else np.nan
        last_surv = 1.0 - last_kpi if pd.notna(last_kpi) else np.nan

        k1, k2, k3 = st.columns(3, gap="large")
        k1.metric("Salidas (total en rango)", fmt_int_es(total_salidas))
        k2.metric("Existencias promedio (rango)", fmt_es(exist_prom_rango, 1))
        k3.metric(f"Supervivencia 30 días (último periodo)", "-" if np.isnan(last_surv) else f"{last_surv*100:.1f}%".replace(".", ","))

        # ---- Gráfico 1: KPI deserción 30 + MA3 + Meta (roja)
        st.markdown("### KPI: **1 - Supervivencia a 30 días** (Deserción 30d)")
        if kpi_period["kpi_desercion30"].dropna().empty:
            st.info("No hay cohortes con follow-up completo (ini <= hoy-30) en el rango.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=kpi_period["Periodo"].astype(str),
                y=kpi_period["kpi_desercion30"],
                mode="lines+markers",
                name="Deserción 30d",
            ))
            fig.add_trace(go.Scatter(
                x=kpi_period["Periodo"].astype(str),
                y=kpi_period["MA3"],
                mode="lines",
                name="Promedio móvil (3)",
            ))

            if pd.notna(meta_val):
                fig.add_trace(go.Scatter(
                    x=kpi_period["Periodo"].astype(str),
                    y=[meta_val] * len(kpi_period),
                    mode="lines",
                    name="Meta (promedio 3 últimos registros del año pasado)",
                    line=dict(color="red", dash="dash"),
                ))

            fig.update_yaxes(tickformat=".0%", range=[0, 1])
            fig.update_layout(
                title="Deserción 30d + Promedio móvil (3) + Meta",
                legend=dict(orientation="h"),
                margin=dict(b=80),
            )
            fig = nice_xaxis(fig)
            fig = apply_line_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True)

        # ---- Gráfico 2: Salidas (barras) y Existencias promedio (línea)
        st.markdown("### Existencias & Salidas (por periodo)")
        if df_period.empty:
            st.info(MSG_NO_DATA_FOR_VIEW)
        else:
            fig2 = make_subplots(specs=[[{"secondary_y": True}]])
            fig2.add_trace(
                go.Bar(
                    x=df_period["Periodo"].astype(str),
                    y=df_period["Salidas"].astype(float),
                    name="Salidas",
                    text=(df_period["Salidas"].round(0).astype(int).astype(str) if show_labels else None),
                    textposition=("outside" if show_labels else None),
                ),
                secondary_y=False,
            )
            fig2.add_trace(
                go.Scatter(
                    x=df_period["Periodo"].astype(str),
                    y=df_period["Existencias_Prom"].astype(float),
                    mode="lines+markers",
                    name="Existencias (promedio)",
                ),
                secondary_y=True,
            )
            fig2.update_layout(
                title=f"Salidas (barras) y Existencias promedio (línea) — Agrupado por {period_label}",
                legend=dict(orientation="h"),
                margin=dict(b=80),
            )
            fig2.update_yaxes(title_text="Salidas", secondary_y=False)
            fig2.update_yaxes(title_text="Existencias (promedio)", secondary_y=True)
            fig2 = nice_xaxis(fig2)
            fig2 = apply_line_labels(fig2, show_labels)
            st.plotly_chart(fig2, use_container_width=True)

        # ---- Descargas (limpias)
        with st.expander("Descargar (Excel) / Ver datos base", expanded=False):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_daily.to_excel(writer, index=False, sheet_name="Diario")
                df_period.to_excel(writer, index=False, sheet_name="Periodo")
                kpi_period.to_excel(writer, index=False, sheet_name="KPI_Desercion30")
                df_sal_det.to_excel(writer, index=False, sheet_name="Salidas_Detalle")
            st.download_button(
                "Descargar Excel (Diario + Periodo + KPI + Salidas Detalle)",
                data=buf.getvalue(),
                file_name="rrhh_panel_limpio.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_panel_limpio",
            )

            st.caption("Vista rápida (solo para auditoría, no es el foco del panel).")
            st.dataframe(_safe_table_for_streamlit(df_period), use_container_width=True, height=260)

    # =============================================================================
    # VIEW 2: DESCRIPTIVOS (BARRAS + PASTEL) — DINÁMICO
    # =============================================================================
    else:
        st.subheader("Descriptivos (Existencias & Salidas)")

        # ---- Dataset Existencias (snapshot) con buckets
        df_now = df0_f[(df0_f["ini"] <= snap_dt) & (df0_f["fin_eff"] >= snap_dt)].copy()
        if not df_now.empty:
            df_now = df_now.sort_values(["cod", "ini"]).groupby("cod", as_index=False).tail(1).copy()
            df_now["ref"] = snap_dt
            df_now["antig_dias"] = (df_now["ref"] - df_now["ini"]).dt.days
            df_now["Antigüedad"] = bucket_antiguedad(df_now["antig_dias"])
            df_now["Edad"] = bucket_edad_from_dob(df_now["fnac"], df_now["ref"])
            # aplicar buckets como filtro también (si están activos)
            if fs.antig:
                df_now = df_now[df_now["Antigüedad"].isin(fs.antig)]
            if fs.edad:
                df_now = df_now[df_now["Edad"].isin(fs.edad)]

        # ---- Dataset Salidas (en rango) ya lo tenemos: df_sal_det
        df_exit = df_sal_det.copy() if df_sal_det is not None else pd.DataFrame()
        # df_sal_det ya incluye Antigüedad y Edad calculados

        # KPIs
        c1, c2, c3 = st.columns(3, gap="large")
        c1.metric("Existencias (snapshot)", fmt_int_es(len(df_now)) if df_now is not None else "0")
        c2.metric("Salidas (rango)", fmt_int_es(len(df_exit)) if df_exit is not None else "0")
        # ratio simple
        ratio = (len(df_exit) / len(df_now)) if (df_now is not None and len(df_now) > 0 and df_exit is not None) else np.nan
        c3.metric("Salidas / Existencias (simple)", "-" if np.isnan(ratio) else f"{ratio*100:.1f}%".replace(".", ","))

        # Selector dataset y variables
        ds_pick = st.selectbox(LBL_OPT_DESC_DATASET, [LBL_OPT_DESC_DATASET_1, LBL_OPT_DESC_DATASET_2], index=0, key="desc_dataset_pick")
        if ds_pick == LBL_OPT_DESC_DATASET_1:
            dset = df_now.copy() if df_now is not None else pd.DataFrame()
            ds_title = f"Existencias (snapshot {snap_dt.date()})"
        else:
            dset = df_exit.copy() if df_exit is not None else pd.DataFrame()
            ds_title = f"Salidas (rango {start_dt.date()} a {end_dt.date()})"

        if dset is None or dset.empty:
            st.info(MSG_NO_DATA_FOR_VIEW)
            st.stop()

        # Variables seleccionadas (dinámico) -> se pintan todas las que elijas
        if not desc_vars:
            st.info("Selecciona al menos 1 variable en Opciones → Variables descriptivas.")
            st.stop()

        st.markdown(f"### {ds_title} — Barras y Pastel")
        for friendly in desc_vars:
            col = desc_vars_catalog.get(friendly)
            if col is None or col not in dset.columns:
                continue

            # Enriquecer labels si es Edad/Antigüedad pero no existe (por si dataset)
            if col in ("Edad", "Antigüedad") and col not in dset.columns:
                continue

            df_counts = counts_topn_with_otros(dset[col], topn=topn)
            if df_counts.empty:
                continue

            b, p = bar_and_pie(df_counts, title=f"{friendly} ({ds_title})", show_labels=show_labels, topn=topn)
            left, right = st.columns([1, 1], gap="large")
            with left:
                st.plotly_chart(b, use_container_width=True)
            with right:
                st.plotly_chart(p, use_container_width=True)

        # Descarga snapshot/salidas
        with st.expander("Descargar datasets descriptivos (Excel)", expanded=False):
            buf2 = io.BytesIO()
            with pd.ExcelWriter(buf2, engine="openpyxl") as writer:
                if df_now is not None and not df_now.empty:
                    df_now.to_excel(writer, index=False, sheet_name="Existencias_Snapshot")
                if df_exit is not None and not df_exit.empty:
                    df_exit.to_excel(writer, index=False, sheet_name="Salidas_Rango")
            st.download_button(
                "Descargar Excel (Existencias + Salidas)",
                data=buf2.getvalue(),
                file_name="rrhh_descriptivos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_desc",
            )
