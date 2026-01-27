# -*- coding: utf-8 -*-
from __future__ import annotations

# =============================================================================
# 0) TÍTULOS / TEXTOS (80% de cambios deberían vivir aquí)
# =============================================================================
APP_TITLE = "Panel TTHH"
APP_SUBTITLE = (
    "Existencias • Salidas • KPI: Deserción 30D Estandarizada "
    "+ Promedio móvil (3) + Meta (promedio 3 últimos registros del año pasado)"
)

# UI (layout / navegación)
LBL_SHOW_FILTERS = "Mostrar panel (cargar datos / filtros / opciones)"
LBL_VIEW_PICK = "Vista"
VIEW_1 = "Dashboard"
VIEW_2 = "Descriptivos (Existencias & Salidas)"

PANEL_TITLE = "Panel de control"
TAB_DATA = "Datos & Periodo"
TAB_FILTERS = "Filtros"
TAB_OPTIONS = "Opciones"

# Inputs
LBL_UPLOAD_MAIN = "Sube Excel/CSV (Historia Personal)"
LBL_PATH_MAIN = "O ruta local (opcional)"
LBL_SHEET_MAIN = "Hoja (Historia Personal)"

LBL_RANGE_PRESET = "Atajo de rango"
LBL_RANGE_SLIDER = "Inicio / Fin"
LBL_GROUP_BY = "Agrupar por"
LBL_SNAPSHOT_DATE = "Snapshot (día)"
LBL_TODAY_CUT = "Hoy (corte)"

# Filtros
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
LBL_OPT_EXIT_SHARE_VAR = "Salidas como % del total de existencias (elige variable)"

# Mensajes
MSG_NEED_DATA = "Carga datos y define rango/filtros para ver el panel."
MSG_LOAD_FILE_TO_START = "Carga un archivo para iniciar."
MSG_PATH_NOT_FOUND = "La ruta no existe."
MSG_READ_FAIL = "No se pudo leer el archivo:"
MSG_NO_DATA_FOR_VIEW = "No hay datos suficientes con los filtros actuales."
