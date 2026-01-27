# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Tuple
import plotly.express as px
import plotly.graph_objects as go

from rrhh_panel.viz.labels import apply_bar_labels

def bar_and_pie(df_counts, title: str, show_labels: bool) -> Tuple[go.Figure, go.Figure]:
    d = df_counts.copy().sort_values("N", ascending=True)
    figb = px.bar(d, x="N", y="Categoria", orientation="h", title=title)
    figb = apply_bar_labels(figb, show_labels, orientation="h")

    figp = px.pie(df_counts, names="Categoria", values="N", title=title)
    figp.update_traces(textinfo="label+percent" if show_labels else "percent")
    return figb, figp
