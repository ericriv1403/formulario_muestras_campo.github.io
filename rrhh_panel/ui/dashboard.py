# -*- coding: utf-8 -*-
from __future__ import annotations

import io
from datetime import date
import numpy as np
import pandas as pd
import streamlit as st

from rrhh_panel.config.params import H_DAYS, MIN_BASE_KPI, MIN_COVERAGE_W
from rrhh_panel.filters.apply import apply_categorical_filters
from rrhh_panel.preprocessing.historia_personal import merge_intervals_per_person
from rrhh_panel.metrics.existencias_salidas import compute_salidas_daily_filtered, compute_existencias_daily_filtered_fast
from rrhh_panel.time_windows.aggregate import aggregate_daily_to_period_simple
from rrhh_panel.utils.dates import add_calendar_fields
from rrhh_panel.metrics.kpi_ds30_std_v1 import (
    compute_standard_weights_from_baseline,
    compute_ds30_std_by_period,
    meta_from_last_year_last3,
)
from rrhh_panel.viz.dashboard_figs import fig_kpi_ds30, fig_exist_salidas
from rrhh_panel.utils.formatting import fmt_es, fmt_int_es
from rrhh_panel.utils.safe import safe_table_for_streamlit
from rrhh_panel.config.texts import MSG_NO_DATA_FOR_VIEW

def render_dashboard(*, g: dict, fs, opts: dict) -> None:
    df0 = g["df0"]
    start_dt = g["start_dt"]
    end_dt = g["end_dt"]
    period = g["period"]
    period_label = g["period_label"]
    cut_today = g["cut_today"]
    min_date = g["min_date"]
    max_date = g["max_date"]

    unique_personas_por_dia = bool(opts["unique_personas_por_dia"])
    show_labels = bool(opts["show_labels"])
    topn = int(opts["topn"])

    # 1) Filtros categóricos
    df0_f = apply_categorical_filters(df0, fs)
    if df0_f.empty:
        st.warning(MSG_NO_DATA_FOR_VIEW)
        st.stop()

    # 2) Series diarias Existencias/Salidas
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

    # 3) KPI DS30-STD + MA3 + Meta + flags
    with st.spinner("Calculando KPI robusto (Deserción 30D estandarizada) + meta..."):
        last_year = int(end_dt.year) - 1
        base_start = pd.Timestamp(date(last_year, 1, 1))
        base_end = pd.Timestamp(date(last_year, 12, 31))

        if pd.notna(min_date):
            base_start = max(base_start, pd.Timestamp(min_date).normalize())
        if pd.notna(max_date):
            base_end = min(base_end, pd.Timestamp(max_date).normalize())

        weights = compute_standard_weights_from_baseline(
            df_events_baseline=df0,
            period=period,
            ref_start=base_start,
            ref_end=base_end,
        )

        kpi_period = compute_ds30_std_by_period(
            df_events_filtered=df0_f,
            start=start_dt,
            end=end_dt,
            period=period,
            cut_today=cut_today,
            weights=weights,
            H_days=H_DAYS,
            min_base=MIN_BASE_KPI,
        )

        kpi_period = kpi_period.sort_values("cut").reset_index(drop=True)
        kpi_period["MA3"] = kpi_period["DS30_std"].rolling(window=3, min_periods=1).mean()

        kpi_base = compute_ds30_std_by_period(
            df_events_filtered=df0,
            start=base_start,
            end=base_end,
            period=period,
            cut_today=cut_today,
            weights=weights,
            H_days=H_DAYS,
            min_base=MIN_BASE_KPI,
        )
        meta_val = meta_from_last_year_last3(kpi_base, end_dt=end_dt, value_col="DS30_std")
        kpi_period["Meta"] = meta_val

        kpi_period["flag_text"] = ""
        kpi_period.loc[kpi_period["flag_incomplete_30d"] == True, "flag_text"] = "INCOMPLETO 30D"
        kpi_period.loc[(kpi_period["flag_text"] == "") & (kpi_period["flag_base_baja"] == True), "flag_text"] = f"BASE BAJA (<{MIN_BASE_KPI})"
        kpi_period.loc[(kpi_period["flag_text"] == "") & (kpi_period["coverage_w"] < MIN_COVERAGE_W), "flag_text"] = f"COBERTURA < {int(MIN_COVERAGE_W*100)}%"

    # =============================================================================
    # VIEW: DASHBOARD
    # =============================================================================
    st.subheader("Dashboard")

    total_salidas = float(df_period["Salidas"].sum()) if not df_period.empty else 0.0
    exist_prom_rango = float(np.nanmean(df_period["Existencias_Prom"].values)) if not df_period.empty else np.nan

    kpi_last = kpi_period.dropna(subset=["DS30_std"]).tail(1)
    last_ds30 = float(kpi_last["DS30_std"].iloc[0]) if not kpi_last.empty else np.nan
    last_surv30 = (1.0 - last_ds30) if pd.notna(last_ds30) else np.nan

    k1, k2, k3 = st.columns(3, gap="large")
    k1.metric("Salidas (total en rango)", fmt_int_es(total_salidas))
    k2.metric("Existencias promedio (rango)", fmt_es(exist_prom_rango, 1))
    k3.metric(
        "Supervivencia 30D (último periodo, std)",
        "-" if np.isnan(last_surv30) else f"{last_surv30*100:.1f}%".replace(".", ","),
    )

    st.markdown("### KPI: **Deserción 30D Estandarizada (Edad×Antigüedad)**")
    if kpi_period["DS30_std"].dropna().empty:
        st.info("No hay periodos con follow-up completo (cut+30 <= hoy) y/o base suficiente con los filtros actuales.")
    else:
        fig = fig_kpi_ds30(kpi_period, meta_val=meta_val, show_labels=show_labels, min_base_kpi=MIN_BASE_KPI)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Existencias & Salidas (por periodo)")
    if df_period.empty:
        st.info(MSG_NO_DATA_FOR_VIEW)
    else:
        fig2 = fig_exist_salidas(df_period, period_label=period_label, show_labels=show_labels)
        st.plotly_chart(fig2, use_container_width=True)

    from rrhh_panel.ui.downloads import downloads_panel
    downloads_panel(df_daily=df_daily, df_period=df_period, kpi_period=kpi_period, df_sal_det=df_sal_det, weights=weights)
