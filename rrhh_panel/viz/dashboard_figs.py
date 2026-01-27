# -*- coding: utf-8 -*-
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from rrhh_panel.viz.labels import nice_xaxis, apply_line_labels
from rrhh_panel.utils.formatting import fmt_es

def fig_kpi_ds30(kpi_period, meta_val: float | None, show_labels: bool, min_base_kpi: int) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=kpi_period["Periodo"].astype(str),
        y=kpi_period["DS30_std"],
        mode="lines+markers",
        name="DS30-STD",
        customdata=np.stack([
            kpi_period["N"].fillna(0).astype(float),
            kpi_period["E"].fillna(0).astype(float),
            kpi_period["coverage_w"].fillna(0.0).astype(float),
            kpi_period["DS30_raw"].astype(float),
            kpi_period["flag_text"].astype(str),
        ], axis=1),
        hovertemplate=(
            "<b>Periodo</b>: %{x}<br>"
            "<b>DS30-STD</b>: %{y:.2%}<br>"
            "<b>N activos (cut)</b>: %{customdata[0]:.0f}<br>"
            "<b>E salen <=30d</b>: %{customdata[1]:.0f}<br>"
            "<b>DS30-RAW</b>: %{customdata[3]:.2%}<br>"
            "<b>Cobertura pesos</b>: %{customdata[2]:.0%}<br>"
            "<b>Nota</b>: %{customdata[4]}<extra></extra>"
        ),
    ))

    fig.add_trace(go.Scatter(
        x=kpi_period["Periodo"].astype(str),
        y=kpi_period["MA3"],
        mode="lines",
        name="Promedio móvil (3)",
        hovertemplate="<b>Periodo</b>: %{x}<br><b>MA3</b>: %{y:.2%}<extra></extra>",
    ))

    if meta_val is not None and not np.isnan(meta_val):
        fig.add_trace(go.Scatter(
            x=kpi_period["Periodo"].astype(str),
            y=[meta_val] * len(kpi_period),
            mode="lines",
            name="Meta (promedio 3 últimos registros del año pasado)",
            line=dict(color="red", dash="dash"),
            hovertemplate="<b>Meta</b>: %{y:.2%}<extra></extra>",
        ))

    if show_labels:
        mask_flag = (kpi_period["flag_text"].astype(str) != "") & (~kpi_period["Periodo"].isna())
        if mask_flag.any():
            y_flag = kpi_period.loc[mask_flag, "DS30_std"].copy()
            fallback_y = (meta_val if (meta_val is not None and not np.isnan(meta_val)) else 0.01)
            y_flag = y_flag.fillna(fallback_y)
            fig.add_trace(go.Scatter(
                x=kpi_period.loc[mask_flag, "Periodo"].astype(str),
                y=y_flag,
                mode="markers+text",
                text=kpi_period.loc[mask_flag, "flag_text"].astype(str),
                textposition="top center",
                showlegend=False,
                hoverinfo="skip",
            ))

    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    fig.update_layout(
        title="Deserción 30D Estandarizada + Promedio móvil (3) + Meta",
        legend=dict(orientation="h"),
        margin=dict(b=80),
    )
    fig = nice_xaxis(fig)
    fig = apply_line_labels(fig, show_labels)
    return fig

def fig_exist_salidas(df_period, period_label: str, show_labels: bool) -> go.Figure:
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
            hovertemplate="<b>Periodo</b>: %{x}<br><b>Existencias prom</b>: %{y:.1f}<extra></extra>",
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
    return fig2
