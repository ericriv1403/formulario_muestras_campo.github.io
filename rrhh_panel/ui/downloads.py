# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import pandas as pd
import streamlit as st

from rrhh_panel.utils.safe import safe_table_for_streamlit

def downloads_panel(*, df_daily, df_period, kpi_period, df_sal_det, weights) -> None:
    with st.expander("Descargar (Excel) / Ver datos base", expanded=False):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_daily.to_excel(writer, index=False, sheet_name="Diario")
            df_period.to_excel(writer, index=False, sheet_name="Periodo")
            kpi_period.to_excel(writer, index=False, sheet_name="KPI_DS30_STD")
            df_sal_det.to_excel(writer, index=False, sheet_name="Salidas_Detalle")
            weights.to_excel(writer, index=False, sheet_name="Pesos_Estrato")

        st.download_button(
            "Descargar Excel (Diario + Periodo + KPI + Salidas Detalle + Pesos)",
            data=buf.getvalue(),
            file_name="rrhh_panel_limpio.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_panel_limpio",
        )

        st.caption("Vista rápida (solo para auditoría).")
        st.dataframe(safe_table_for_streamlit(kpi_period.tail(30)), use_container_width=True, height=260)
