# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import numpy as np
import pandas as pd
import streamlit as st

from rrhh_panel.filters.apply import apply_categorical_filters
from rrhh_panel.features.buckets import bucket_antiguedad, bucket_edad_from_dob
from rrhh_panel.descriptives.topn import counts_topn_with_otros
from rrhh_panel.descriptives.shares import compute_exit_share_of_total_existences
from rrhh_panel.viz.charts import bar_and_pie
from rrhh_panel.viz.descriptives_figs import fig_exit_share
from rrhh_panel.utils.formatting import fmt_int_es, fmt_es
from rrhh_panel.config.texts import (
    MSG_NO_DATA_FOR_VIEW,
    LBL_OPT_DESC_DATASET, LBL_OPT_DESC_DATASET_1, LBL_OPT_DESC_DATASET_2,
)
from rrhh_panel.time_windows.aggregate import aggregate_daily_to_period_simple

def render_descriptives(*, g: dict, fs, opts: dict) -> None:
    df0 = g["df0"]
    start_dt = g["start_dt"]
    end_dt = g["end_dt"]
    period = g["period"]
    snap_dt = g["snap_dt"]

    show_labels = bool(opts["show_labels"])
    topn = int(opts["topn"])
    desc_vars = list(opts["desc_vars"])
    desc_vars_catalog = dict(opts["desc_vars_catalog"])
    exit_share_var = str(opts.get("exit_share_var", "Área General"))
    exit_share_col = desc_vars_catalog.get(exit_share_var, "area_gen")

    df0_f = apply_categorical_filters(df0, fs)
    if df0_f.empty:
        st.warning(MSG_NO_DATA_FOR_VIEW)
        st.stop()

    # ---- Dataset Existencias (snapshot) con buckets
    df_now = df0_f[(df0_f["ini"] <= snap_dt) & (df0_f["fin_eff"] >= snap_dt)].copy()
    if not df_now.empty:
        df_now = df_now.sort_values(["cod", "ini"]).groupby("cod", as_index=False).tail(1).copy()
        df_now["ref"] = snap_dt
        df_now["antig_dias"] = (df_now["ref"] - df_now["ini"]).dt.days
        df_now["Antigüedad"] = bucket_antiguedad(df_now["antig_dias"])
        df_now["Edad"] = bucket_edad_from_dob(df_now["fnac"], df_now["ref"])
        if fs.antig:
            df_now = df_now[df_now["Antigüedad"].isin(fs.antig)]
        if fs.edad:
            df_now = df_now[df_now["Edad"].isin(fs.edad)]

    # ---- Dataset Salidas (en rango)
    d = df0_f[~df0_f["fin"].isna()].copy()
    d = d[(d["fin"] >= start_dt) & (d["fin"] <= end_dt)].copy()
    df_exit = d.copy()

    st.subheader("Descriptivos (Existencias & Salidas)")

    c1, c2, c3 = st.columns(3, gap="large")
    c1.metric("Existencias (snapshot)", fmt_int_es(len(df_now)) if df_now is not None else "0")
    c2.metric("Salidas (rango)", fmt_int_es(len(df_exit)) if df_exit is not None else "0")
    ratio = (len(df_exit) / len(df_now)) if (df_now is not None and len(df_now) > 0 and df_exit is not None) else np.nan
    c3.metric("Salidas / Existencias (simple)", "-" if np.isnan(ratio) else f"{ratio*100:.1f}%".replace(".", ","))

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

    if not desc_vars:
        st.info("Selecciona al menos 1 variable en Opciones → Variables descriptivas.")
        st.stop()

    st.markdown(f"### {ds_title} — Barras y Pastel")
    for friendly in desc_vars:
        col = desc_vars_catalog.get(friendly)
        if col is None or col not in dset.columns:
            continue

        df_counts = counts_topn_with_otros(dset[col], topn=topn)
        if df_counts.empty:
            continue

        b, p = bar_and_pie(df_counts, title=f"{friendly} ({ds_title})", show_labels=show_labels)
        left, right = st.columns([1, 1], gap="large")
        with left:
            st.plotly_chart(b, use_container_width=True)
        with right:
            st.plotly_chart(p, use_container_width=True)

    # ---------------------------------------------------------------------
    # Salidas como % del total de existencias
    # ---------------------------------------------------------------------
    st.markdown("### Salidas como % del total de existencias (del grupo filtrado)")

    # Base: existencias promedio del rango (aprox). Si no tienes df_period aquí, usa snapshot.
    total_exist_base = float(len(df_now)) if df_now is not None else np.nan
    if np.isnan(total_exist_base) or total_exist_base <= 0:
        total_exist_base = float(len(df_now))

    if df_exit is None or df_exit.empty:
        st.info("No hay salidas en el rango para graficar proporciones.")
    else:
        if exit_share_col not in df_exit.columns:
            st.info("No se pudo construir el gráfico: la variable seleccionada no existe en el dataset de salidas.")
        else:
            dshare = compute_exit_share_of_total_existences(
                df_now=df_now if df_now is not None else pd.DataFrame(),
                df_exit=df_exit,
                dim_col=exit_share_col,
                topn=topn,
                total_exist_base=total_exist_base,
            )
            if dshare.empty:
                st.info("No hay datos suficientes para el gráfico de proporciones.")
            else:
                figx = fig_exit_share(
                    dshare,
                    title=f"{exit_share_var}: Salidas como % del total de existencias (base = existencias snapshot)",
                    show_labels=show_labels,
                )
                st.plotly_chart(figx, use_container_width=True)

                st.caption(
                    f"Base usada: Existencias snapshot = {fmt_es(total_exist_base,1)}. "
                    "En el hover también ves la tasa sobre su propia área (Salidas/ExistSnapshot)."
                )

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
