# RRHH Panel (Streamlit) — Modular

Este repo es el refactor modular del **Panel TTHH** (Existencias, Salidas, KPI DS30-STD, Descriptivos, Descargas).

## Ejecutar
1) Crear entorno (opcional) y luego:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Dónde cambiar cosas (regla: “una razón = un módulo”)
- **Textos / labels / nombres de vistas**: `rrhh_panel/config/texts.py`
- **Parámetros de negocio (H=30, min base KPI, defaults, topN, etc.)**: `rrhh_panel/config/params.py`
- **Contrato de datos (columnas requeridas, mapeo interno, candidates de %R)**: `rrhh_panel/schema/historia_personal.py`
- **Catálogos de negocio (áreas / clasificaciones)**: `rrhh_panel/references/*.py`
- **Lectura de datos (Excel/CSV, reglas estrictas de columnas)**: `rrhh_panel/data_io/read hookup`
  - `rrhh_panel/data_io/readers.py`
- **Limpieza / preparación**: `rrhh_panel/preprocessing/historia_personal.py`
- **Buckets (edad / antigüedad) y estratos**: `rrhh_panel/features/buckets.py`
- **Filtros (estado + aplicación)**: `rrhh_panel/filters/*`
- **Ventanas temporales / agregación a periodos**: `rrhh_panel/time_windows/*`
- **KPIs y métricas (cálculo puro, sin UI)**: `rrhh_panel/metrics/*`
- **Descriptivos**: `rrhh_panel/descriptives/*`
- **Gráficos (Plotly), sin cálculo**: `rrhh_panel/viz/*`
- **UI Streamlit**: `rrhh_panel/ui/*`
- **Orquestador**: `app.py`

## Theming / CSS
- Streamlit theme: `.streamlit/config.toml`
- CSS adicional: `rrhh_panel/assets/style.css`
- Carga de CSS: `rrhh_panel/ui/theming.py`

## Versionar KPI
- KPI actual: `rrhh_panel/metrics/kpi_ds30_std_v1.py`
- Si quieres v2: duplica el archivo y cambia el import en `rrhh_panel/ui/dashboard.py`.

## Notas
- Este diseño permite migrar a Dash/Altair tocando casi solo `rrhh_panel/ui/*` y/o `rrhh_panel/viz/*`.
