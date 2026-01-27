# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict
import numpy as np
import pandas as pd
import streamlit as st

from rrhh_panel.preprocessing.historia_personal import merge_intervals_per_person
from rrhh_panel.time_windows.windows import build_period_windows
from rrhh_panel.features.buckets import make_stratum

@st.cache_data(show_spinner=False)
def compute_standard_weights_from_baseline(
    df_events_baseline: pd.DataFrame,
    period: str,
    ref_start: pd.Timestamp,
    ref_end: pd.Timestamp,
) -> pd.DataFrame:
    # pesos w_s = composición acumulada de snapshots en baseline
    if df_events_baseline is None or df_events_baseline.empty:
        return pd.DataFrame(columns=["Estrato", "w"])

    df_int = merge_intervals_per_person(df_events_baseline)
    windows = build_period_windows(ref_start, ref_end, period)
    if windows.empty:
        return pd.DataFrame(columns=["Estrato", "w"])

    acc: Dict[str, int] = {}
    for _, w in windows.iterrows():
        cut = pd.Timestamp(w["cut"]).normalize()
        active = df_int[(df_int["ini"] <= cut) & (df_int["fin_eff"] >= cut)].copy()
        if active.empty:
            continue
        active = active.sort_values(["cod", "ini"]).groupby("cod", as_index=False).tail(1).copy()
        active = make_stratum(active, cut)
        cts = active.groupby("Estrato")["cod"].nunique()
        for k, v in cts.items():
            acc[k] = acc.get(k, 0) + int(v)

    if not acc:
        return pd.DataFrame(columns=["Estrato", "w"])

    w = pd.DataFrame({"Estrato": list(acc.keys()), "count": list(acc.values())})
    w["w"] = w["count"] / float(w["count"].sum())
    return w[["Estrato", "w"]].sort_values("w", ascending=False).reset_index(drop=True)

@st.cache_data(show_spinner=False)
def compute_ds30_std_by_period(
    df_events_filtered: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    period: str,
    cut_today: pd.Timestamp,
    weights: pd.DataFrame,
    H_days: int = 30,
    min_base: int = 30,
) -> pd.DataFrame:
    if df_events_filtered is None or df_events_filtered.empty:
        return pd.DataFrame()

    df_int = merge_intervals_per_person(df_events_filtered)
    windows = build_period_windows(start, end, period).copy()
    if windows.empty:
        return pd.DataFrame()

    ct = pd.Timestamp(cut_today).normalize()
    H = int(H_days)

    wdf = weights.copy() if weights is not None else pd.DataFrame(columns=["Estrato", "w"])
    if not wdf.empty:
        wdf = wdf.dropna(subset=["Estrato", "w"]).copy()
        wdf["Estrato"] = wdf["Estrato"].astype(str)
        wdf["w"] = pd.to_numeric(wdf["w"], errors="coerce")

    rows = []
    for _, w in windows.iterrows():
        cut = pd.Timestamp(w["cut"]).normalize()
        flag_incomplete = bool((cut + pd.Timedelta(days=H)) > ct)

        active = df_int[(df_int["ini"] <= cut) & (df_int["fin_eff"] >= cut)].copy()
        if active.empty:
            rows.append({
                "Periodo": w["Periodo"],
                "cut": cut,
                "N": 0,
                "E": 0,
                "DS30_raw": np.nan,
                "DS30_std": np.nan,
                "coverage_w": 0.0,
                "flag_incomplete_30d": flag_incomplete,
                "flag_base_baja": True,
            })
            continue

        active = active.sort_values(["cod", "ini"]).groupby("cod", as_index=False).tail(1).copy()
        active = make_stratum(active, cut)

        # Evento en 30 días: fin real en (cut, cut+H]
        active["evento_30d"] = (~active["fin"].isna()) & (active["fin"] > cut) & (active["fin"] <= (cut + pd.Timedelta(days=H)))

        N = int(active["cod"].nunique())
        E = int(active.loc[active["evento_30d"], "cod"].nunique())
        ds_raw = (float(E) / float(N)) if N > 0 else np.nan

        # Estándar: p_s por estrato
        tab = active.groupby("Estrato").agg(
            N_s=("cod", "nunique"),
            E_s=("evento_30d", "sum"),
        ).reset_index()
        tab["p_s"] = np.where(tab["N_s"] > 0, tab["E_s"] / tab["N_s"], np.nan)

        ds_std = np.nan
        coverage = 0.0
        if (wdf is not None) and (not wdf.empty):
            j = wdf.merge(tab[["Estrato", "p_s"]], on="Estrato", how="left")
            mask = ~j["p_s"].isna() & ~j["w"].isna()
            coverage = float(j.loc[mask, "w"].sum()) if mask.any() else 0.0
            if coverage > 0:
                ds_std = float((j.loc[mask, "w"] * j.loc[mask, "p_s"]).sum() / coverage)
        else:
            ds_std = ds_raw
            coverage = 1.0 if pd.notna(ds_raw) else 0.0

        flag_base_baja = bool(N < int(min_base))

        # si es incompleto, dejamos NaN (para no engañar la tendencia)
        if flag_incomplete:
            ds_raw_out = np.nan
            ds_std_out = np.nan
        else:
            ds_raw_out = ds_raw
            ds_std_out = ds_std

        rows.append({
            "Periodo": w["Periodo"],
            "cut": cut,
            "N": N,
            "E": E,
            "DS30_raw": ds_raw_out,
            "DS30_std": ds_std_out,
            "coverage_w": coverage,
            "flag_incomplete_30d": flag_incomplete,
            "flag_base_baja": flag_base_baja,
        })

    out = pd.DataFrame(rows).sort_values("cut").reset_index(drop=True)
    return out

def meta_from_last_year_last3(df_metric: pd.DataFrame, end_dt: pd.Timestamp, value_col: str) -> float:
    if df_metric is None or df_metric.empty or value_col not in df_metric.columns:
        return np.nan
    last_year = int(pd.Timestamp(end_dt).year) - 1
    d = df_metric.copy()
    d["cut"] = pd.to_datetime(d["cut"], errors="coerce")
    d = d[d["cut"].dt.year == last_year].copy()
    d = d.dropna(subset=[value_col]).sort_values("cut")
    if d.empty:
        return np.nan
    tail = d[value_col].tail(3)
    if tail.empty:
        return np.nan
    return float(np.nanmean(tail.values))
