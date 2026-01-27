# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from datetime import date
import pandas as pd
import streamlit as st

from rrhh_panel.config.texts import (
    PANEL_TITLE, TAB_DATA, TAB_FILTERS, TAB_OPTIONS,
    LBL_UPLOAD_MAIN, LBL_PATH_MAIN, LBL_SHEET_MAIN,
    LBL_RANGE_PRESET, LBL_RANGE_SLIDER, LBL_GROUP_BY, LBL_SNAPSHOT_DATE, LBL_TODAY_CUT,
    LBL_FILTERS_HINT, BTN_CLEAR_FILTERS,
    LBL_SEXO, LBL_AREA_GEN, LBL_AREA, LBL_CARGO, LBL_CLAS, LBL_TS, LBL_EMP, LBL_NAC, LBL_LUG, LBL_REG,
    LBL_TENURE_BUCKET, LBL_AGE_BUCKET,
    LBL_OPT_UNIQUE_DAY, LBL_OPT_SHOW_LABELS, LBL_OPT_TOPN,
    LBL_OPT_DESC_VARS, LBL_OPT_EXIT_SHARE_VAR,
    MSG_LOAD_FILE_TO_START, MSG_PATH_NOT_FOUND, MSG_READ_FAIL,
)
from rrhh_panel.config.params import DEFAULT_TOPN, DEFAULT_RANGE_DAYS
from rrhh_panel.data_io.readers import read_csv_any, read_excel_strict_hist
from rrhh_panel.preprocessing.historia_personal import validate_and_prepare_hist, merge_intervals_per_person
from rrhh_panel.filters.state import FilterState
from rrhh_panel.filters.options import options_for_col
from rrhh_panel.features.buckets import TENURE_BUCKETS, AGE_BUCKETS
from rrhh_panel.utils.dates import today_dt

def render_sidebar() -> None:
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
        default_start = max(min_date, default_end - pd.Timedelta(days=DEFAULT_RANGE_DAYS)) if pd.notna(min_date) else (default_end - pd.Timedelta(days=DEFAULT_RANGE_DAYS))

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
            "min_date": min_date,
            "max_date": max_date,
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

        if st.button(BTN_CLEAR_FILTERS, use_container_width=True, key="btn_clear_filters"):
            for k in [
                "f_sexo", "f_area_gen", "f_area", "f_cargo", "f_clas", "f_ts", "f_emp",
                "f_nac", "f_lug", "f_reg", "f_antig", "f_edad",
            ]:
                st.session_state[k] = []
            st.rerun()

        area_gen_pick = st.multiselect(LBL_AREA_GEN, options_for_col(df0, "area_gen"), default=st.session_state.get("f_area_gen", []), key="f_area_gen")

        if area_gen_pick:
            df_area = df0[df0["area_gen"].isin(area_gen_pick)]
            area_opts = options_for_col(df_area, "area")
        else:
            area_opts = options_for_col(df0, "area")

        fs = FilterState(
            sexo=st.multiselect(LBL_SEXO, options_for_col(df0, "sexo"), default=st.session_state.get("f_sexo", []), key="f_sexo"),
            area_gen=area_gen_pick,
            area=st.multiselect(LBL_AREA, area_opts, default=st.session_state.get("f_area", []), key="f_area"),
            cargo=st.multiselect(LBL_CARGO, options_for_col(df0, "cargo"), default=st.session_state.get("f_cargo", []), key="f_cargo"),
            clas=st.multiselect(LBL_CLAS, options_for_col(df0, "clas"), default=st.session_state.get("f_clas", []), key="f_clas"),
            ts=st.multiselect(LBL_TS, options_for_col(df0, "ts"), default=st.session_state.get("f_ts", []), key="f_ts"),
            emp=st.multiselect(LBL_EMP, options_for_col(df0, "emp"), default=st.session_state.get("f_emp", []), key="f_emp"),
            nac=st.multiselect(LBL_NAC, options_for_col(df0, "nac"), default=st.session_state.get("f_nac", []), key="f_nac"),
            lug=st.multiselect(LBL_LUG, options_for_col(df0, "lug"), default=st.session_state.get("f_lug", []), key="f_lug"),
            reg=st.multiselect(LBL_REG, options_for_col(df0, "reg"), default=st.session_state.get("f_reg", []), key="f_reg"),
            antig=st.multiselect(
                LBL_TENURE_BUCKET,
                list(TENURE_BUCKETS.keys()) + ["SIN DATO"],
                default=st.session_state.get("f_antig", []),
                key="f_antig",
            ),
            edad=st.multiselect(
                LBL_AGE_BUCKET,
                list(AGE_BUCKETS.keys()) + ["SIN DATO"],
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
        topn = int(st.number_input(LBL_OPT_TOPN, min_value=5, max_value=30, value=DEFAULT_TOPN, step=1, key="opt_topn"))

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

        default_share = st.session_state.get("opt_exit_share_var", "Área General")
        exit_share_var = st.selectbox(
            LBL_OPT_EXIT_SHARE_VAR,
            options=list(desc_vars_catalog.keys()),
            index=list(desc_vars_catalog.keys()).index(default_share) if default_share in desc_vars_catalog else 0,
            key="opt_exit_share_var",
        )

        st.session_state["__opts__"] = {
            "unique_personas_por_dia": unique_personas_por_dia,
            "show_labels": show_labels,
            "topn": topn,
            "desc_vars": desc_vars,
            "desc_vars_catalog": desc_vars_catalog,
            "exit_share_var": exit_share_var,
        }
