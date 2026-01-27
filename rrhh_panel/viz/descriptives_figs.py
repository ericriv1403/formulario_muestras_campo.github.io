# -*- coding: utf-8 -*-
from __future__ import annotations

import plotly.express as px
from rrhh_panel.viz.labels import apply_bar_labels

def fig_exit_share(dshare, title: str, show_labels: bool):
    figx = px.bar(
        dshare,
        x="PctTotalExist",
        y="Categoria",
        orientation="h",
        title=title,
        hover_data={
            "Salidas": True,
            "ExistSnapshot": True,
            "TasaSobreArea": ":.2f",
            "PctTotalExist": ":.2f",
        },
    )
    figx.update_xaxes(title_text="% del total de existencias (promedio rango)")
    figx.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "<b>Salidas</b>: %{customdata[0]:.0f}<br>"
            "<b>% Total existencias</b>: %{x:.2f}%<br>"
            "<b>Existencias snapshot</b>: %{customdata[1]:.0f}<br>"
            "<b>Tasa sobre su área</b>: %{customdata[2]:.2f}%<extra></extra>"
        )
    )
    figx = apply_bar_labels(figx, show_labels, orientation="h")
    return figx
