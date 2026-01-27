# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st
from rrhh_panel.config.texts import LBL_SHOW_FILTERS, LBL_VIEW_PICK, VIEW_1, VIEW_2

def topbar():
    top = st.container()
    with top:
        c1, c2 = st.columns([1, 2], gap="large")
        with c1:
            show_filters = st.toggle(LBL_SHOW_FILTERS, value=True)
        with c2:
            view = st.radio(LBL_VIEW_PICK, options=[VIEW_1, VIEW_2], horizontal=True, index=0)
    return show_filters, view

def columns_layout(show_filters: bool):
    if show_filters:
        col_filters, col_main = st.columns([1, 3], gap="large")
        return col_filters, col_main
    return None, st.container()
