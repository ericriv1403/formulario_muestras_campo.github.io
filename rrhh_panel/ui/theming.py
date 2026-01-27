# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import streamlit as st

def load_css() -> None:
    css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "style.css")
    css_path = os.path.normpath(css_path)
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
