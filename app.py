# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from rrhh_panel.config.texts import APP_TITLE, APP_SUBTITLE
from rrhh_panel.ui.theming import load_css
from rrhh_panel.ui.layout import topbar, columns_layout
from rrhh_panel.ui.sidebar import render_sidebar
from rrhh_panel.ui.dashboard import render_dashboard
from rrhh_panel.ui.descriptives import render_descriptives
from rrhh_panel.config.texts import VIEW_1, VIEW_2, MSG_NEED_DATA, MSG_LOAD_FILE_TO_START
from rrhh_panel.ui.floating_chat import render_floating_chat

context_summary = f"Vista={view} | Periodo={period_label} | Rango={start_dt.date()} a {end_dt.date()}"
render_floating_chat(context_summary=context_summary)

def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    load_css()

    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    show_filters, view = topbar()

    col_filters, col_main = columns_layout(show_filters)

    # Sidebar/panel: carga datos, filtros, opciones
    if show_filters:
        with col_filters:
            render_sidebar()

    # Main: dashboard o descriptivos
    with col_main:
        g = st.session_state.get("__globals__")
        fs = st.session_state.get("__fs__")
        opts = st.session_state.get("__opts__")

        if not g or not fs or not opts:
            st.warning(MSG_NEED_DATA if not show_filters else MSG_LOAD_FILE_TO_START)
            st.stop()

        if view == VIEW_1:
            render_dashboard(g=g, fs=fs, opts=opts)
        else:
            render_descriptives(g=g, fs=fs, opts=opts)

if __name__ == "__main__":
    main()
