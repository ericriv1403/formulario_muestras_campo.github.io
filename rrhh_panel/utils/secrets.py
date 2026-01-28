from __future__ import annotations
import os

def get_secret(name: str, default: str = "") -> str:
    # 1) Streamlit Cloud / local secrets
    try:
        import streamlit as st
        val = st.secrets.get(name, None)
        if val is not None and str(val).strip() != "":
            return str(val)
    except Exception:
        pass

    # 2) Environment variables fallback
    val2 = os.getenv(name, default)
    return val2
