# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple
import numpy as np
import pandas as pd
import streamlit as st

from rrhh_panel.features.buckets import TENURE_BUCKETS, AGE_BUCKETS, bucket_antiguedad, bucket_edad_from_dob
from rrhh_panel.schema.historia_personal import MISSING_LABEL
from rrhh_panel.utils.dates import add_calendar_fields, to_datetime_norm, years_offset_date

@st.cache_data(show_spinner=False)
def compute_existencias_daily_filtered_fast(
    df_intervals: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    antig_sel: List[str],
    edad_sel: List[str],
) -> pd.DataFrame:
    idx = pd.date_range(start, end, freq="D")
    n = len(idx)
    if n == 0:
        return pd.DataFrame({"Día": [], "Existencias": []})

    g = df_intervals[(df_intervals["ini"] <= end) & (df_intervals["fin_eff"] >= start)].copy()
    if g.empty:
        out = pd.DataFrame({"Día": idx, "Existencias": np.zeros(n, dtype=int)})
        return add_calendar_fields(out, "Día")

    use_antig = bool(antig_sel)
    use_edad = bool(edad_sel)

    ini_days = g["ini"].values.astype("datetime64[D]").astype("int64")
    fin_days = g["fin_eff"].values.astype("datetime64[D]").astype("int64")
    start_day = np.datetime64(start, "D").astype("int64")
    end_day = np.datetime64(end, "D").astype("int64")

    diff = np.zeros(n + 1, dtype=np.int64)

    antig_list = [b for b in antig_sel if b in TENURE_BUCKETS] if use_antig else []
    edad_list = [b for b in edad_sel if b in AGE_BUCKETS] if use_edad else []
    edad_allow_sindato = use_edad and (MISSING_LABEL in edad_sel)

    fnac_vals = g["fnac"].values

    for i in range(len(g)):
        base_s = max(ini_days[i], start_day)
        base_e = min(fin_days[i], end_day)
        if base_s > base_e:
            continue

        if (not use_antig) and (not use_edad):
            s_idx = int(base_s - start_day)
            e_idx = int(base_e - start_day)
            diff[s_idx] += 1
            diff[e_idx + 1 if (e_idx + 1 < n) else n] -= 1
            continue

        dob_ts = fnac_vals[i]
        dob_missing = pd.isna(dob_ts)
        if use_edad and dob_missing and not edad_allow_sindato:
            continue

        ini0 = ini_days[i]

        # Antig
        if use_antig and antig_list:
            antig_ranges = []
            for b in antig_list:
                a0, a1 = TENURE_BUCKETS[b]
                s = max(ini0 + a0, base_s)
                e = min(base_e, (base_e if a1 is None else ini0 + a1))
                if s <= e:
                    antig_ranges.append((s, e))
            if not antig_ranges:
                continue
        else:
            antig_ranges = [(base_s, base_e)]

        # Edad
        if use_edad and (not dob_missing) and edad_list:
            dob_date = pd.Timestamp(dob_ts).date()
            edad_ranges = []
            for b in edad_list:
                y0, y1 = AGE_BUCKETS[b]
                s_date = start.date() if y0 is None else years_offset_date(dob_date, y0)
                e_date = end.date() if y1 is None else (years_offset_date(dob_date, y1 + 1) - timedelta(days=1))

                s = max(np.int64(np.datetime64(s_date, "D").astype("int64")), base_s)
                e = min(np.int64(np.datetime64(e_date, "D").astype("int64")), base_e)
                if s <= e:
                    edad_ranges.append((s, e))
            if not edad_ranges:
                continue
        else:
            edad_ranges = [(base_s, base_e)]

        # Intersección
        for (as_, ae_) in antig_ranges:
            for (es_, ee_) in edad_ranges:
                s = max(as_, es_)
                e = min(ae_, ee_)
                if s <= e:
                    s_idx = int(s - start_day)
                    e_idx = int(e - start_day)
                    diff[s_idx] += 1
                    diff[e_idx + 1 if (e_idx + 1 < n) else n] -= 1

    exist = np.cumsum(diff[:-1]).astype(int)
    out = pd.DataFrame({"Día": idx, "Existencias": exist})
    return add_calendar_fields(out, "Día")

@st.cache_data(show_spinner=False)
def compute_salidas_daily_filtered(
    df_events: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    antig_sel: List[str],
    edad_sel: List[str],
    unique_personas_por_dia: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    idx = pd.date_range(start, end, freq="D")
    if len(idx) == 0:
        return pd.DataFrame({"Día": [], "Salidas": []}), df_events.iloc[0:0].copy()

    d = df_events[~df_events["fin"].isna()].copy()
    d = d[(d["fin"] >= start) & (d["fin"] <= end)].copy()

    if d.empty:
        out = pd.DataFrame({"Día": idx, "Salidas": np.zeros(len(idx), dtype=int)})
        return add_calendar_fields(out, "Día"), d

    d = d.rename(columns={"fin": "ref_fin"})
    d["ref_fin"] = to_datetime_norm(d["ref_fin"])

    d["antig_dias"] = (d["ref_fin"] - d["ini"]).dt.days
    d["Antigüedad"] = bucket_antiguedad(d["antig_dias"])
    d["Edad"] = bucket_edad_from_dob(d["fnac"], d["ref_fin"])

    if antig_sel:
        d = d[d["Antigüedad"].isin(antig_sel)]
    if edad_sel:
        d = d[d["Edad"].isin(edad_sel)]

    if unique_personas_por_dia:
        g = d.groupby("ref_fin")["cod"].nunique().rename("Salidas")
    else:
        g = d.groupby("ref_fin")["cod"].size().rename("Salidas")

    out = pd.DataFrame({"Día": idx}).merge(
        g.reset_index().rename(columns={"ref_fin": "Día"}),
        on="Día",
        how="left",
    )
    out["Salidas"] = out["Salidas"].fillna(0).astype(int)
    out = add_calendar_fields(out, "Día")
    return out, d
