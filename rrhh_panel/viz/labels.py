# -*- coding: utf-8 -*-
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from rrhh_panel.utils.formatting import fmt_es

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
    # etiqueta solo el último punto de cada serie lineal
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
