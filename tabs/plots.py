"""Zakładka Plots z wykresami pomiarów astronautów."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.colors import qualitative


# Zakładamy, że plik plots.py znajduje się w katalogu tabs,
# a baza astronaut_health_demo_30d.db w katalogu głównym projektu.
DEFAULT_DB = Path(__file__).resolve().parents[1] / "astronaut_health_demo_30d.db"
NASA_RED = "#E4002B"
NASA_BLUE = "#0032A0"


# Etykieta wykresu: (jednostka osi Y, serie z tabeli measurements).
# Zestaw obejmuje wszystkie metric_code znajdujące się w nowej bazie.
# Dwie serie ciśnienia są prezentowane wspólnie na jednym wykresie.
PARAMETERS = {
    # Pomiary monitorowane regularnie
    "Blood pressure": (
        "mmHg",
        (("systolic_mmhg", "Systolic"), ("diastolic_mmhg", "Diastolic")),
    ),
    "Heart rate": ("bpm", (("heart_rate_bpm", "Heart rate"),)),
    "Blood oxygen saturation (SpO₂)": ("%", (("spo2_pct", "SpO₂"),)),
    "Heart rate variability (HRV)": ("ms", (("hrv_rmssd_ms", "RMSSD"),)),
    "Sleep score": ("score / 100", (("sleep_score", "Sleep score"),)),
    "Body mass": ("kg", (("body_mass_kg", "Body mass"),)),
    "Body temperature": ("°C", (("temperature_c", "Body temperature"),)),
    "Respiratory rate": ("breaths/min", (("respiratory_rate_bpm", "Respiratory rate"),)),
    "Hydration (fluid intake)": ("L/day", (("fluid_intake_l", "Fluid intake"),)),
    "Exercise duration": ("min/day", (("exercise_minutes", "Exercise duration"),)),
    "Nutrition score": ("score / 100", (("nutrition_score", "Nutrition score"),)),
    "Cumulative radiation dose": ("mSv", (("radiation_cumulative_msv", "Cumulative dose"),)),
    "Psychological wellbeing": ("score / 100", (("psych_wellbeing_score", "Wellbeing score"),)),
    "Cognitive performance": ("score / 100", (("cognitive_score", "Cognitive score"),)),
    "VO₂ max": ("mL/kg/min", (("vo2max_ml_kg_min", "VO₂ max"),)),
    "Muscle strength index": ("%", (("strength_index_pct", "Strength index"),)),
    "Hearing threshold": ("dB HL", (("hearing_threshold_db_hl", "Hearing threshold"),)),
    "Retinal nerve fiber layer (RNFL)": ("µm", (("rnfl_thickness_um", "RNFL thickness"),)),
    "Jugular vein flow anomaly": ("flag", (("jugular_flow_anomaly_flag", "Flow anomaly"),)),
    "EVA clearance": ("status", (("eva_clearance", "EVA clearance"),)),

    # Pomiary bazowe / specjalistyczne, zwykle bez codziennego powtarzania
    "Height": ("cm", (("height_cm", "Height"),)),
    "Body fat": ("%", (("body_fat_pct", "Body fat"),)),
    "Lean body mass": ("kg", (("lean_mass_kg", "Lean body mass"),)),
    "Bone mineral density": ("g/cm²", (("bone_density_g_cm2", "Bone density"),)),
    "Visual acuity": ("decimal", (("visual_acuity_decimal", "Visual acuity"),)),
    "ECG QTc interval": ("ms", (("ecg_qtc_ms", "QTc interval"),)),
    "Blood glucose": ("mg/dL", (("glucose_mg_dl", "Blood glucose"),)),
    "Hemoglobin": ("g/dL", (("hemoglobin_g_dl", "Hemoglobin"),)),
    "Creatinine": ("mg/dL", (("creatinine_mg_dl", "Creatinine"),)),
    "Sodium": ("mmol/L", (("sodium_mmol_l", "Sodium"),)),
    "Potassium": ("mmol/L", (("potassium_mmol_l", "Potassium"),)),
    "C-reactive protein (CRP)": ("mg/L", (("crp_mg_l", "CRP"),)),
    "Vitamin D": ("ng/mL", (("vitamin_d_ng_ml", "Vitamin D"),)),
    "Urine specific gravity": ("specific gravity", (("urine_specific_gravity", "Urine specific gravity"),)),
}


# Dla flag 0/1 czytelniejsze są etykiety zamiast osi numerycznej.
BINARY_AXIS_LABELS = {
    "jugular_flow_anomaly_flag": {0: "No anomaly", 1: "Anomaly"},
    "eva_clearance": {0: "Not cleared", 1: "Cleared"},
}


def load_database_measurements(database_path: Path) -> pd.DataFrame:
    """Wczytuje pomiary i nazwy astronautów z bazy SQLite w trybie tylko do odczytu."""
    if not database_path.is_file():
        raise FileNotFoundError(f"Database file not found: {database_path}")

    database_uri = database_path.resolve().as_uri() + "?mode=ro"

    with closing(sqlite3.connect(database_uri, uri=True)) as connection:
        readings = pd.read_sql_query(
            """
            SELECT m.astronaut_id,
                   i.name AS astronaut_name,
                   m.measured_at,
                   m.metric_code,
                   m.value
            FROM measurements AS m
            JOIN information AS i ON i.astronaut_id = m.astronaut_id
            ORDER BY m.astronaut_id, m.metric_code, m.measured_at
            """,
            connection,
        )

    if readings.empty:
        return readings

    readings["astronaut_id"] = readings["astronaut_id"].astype(str)
    readings["measured_at"] = pd.to_datetime(
        readings["measured_at"], format="ISO8601", errors="coerce"
    )
    readings["value"] = pd.to_numeric(readings["value"], errors="coerce")
    readings = readings.dropna(subset=["measured_at", "value"])

    return readings


def _resolve_active_astronaut_id(astronaut, astronaut_names: dict) -> str | None:
    """Dopasowuje aktywnego astronautę po ID, a w razie potrzeby po nazwie."""
    candidate_id = getattr(astronaut, "id", None)
    if candidate_id is not None:
        candidate_id = str(candidate_id)
        if candidate_id in astronaut_names:
            return candidate_id

    active_name = getattr(astronaut, "name", None)
    matches = [
        astronaut_id
        for astronaut_id, name in astronaut_names.items()
        if name == active_name
    ]
    return matches[0] if len(matches) == 1 else None


def plots(astronaut) -> None:
    """Wyświetla wykres wybranego parametru dla jednego lub kilku astronautów."""
    st.html(f"""
        <style>
        [data-testid="stMainBlockContainer"] {{
            padding-bottom: 1rem !important;
        }}

        /* Nagłówek i podtytuł strony */
        [data-testid="stMain"] h2 {{
            color: #F8FAFC !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            margin-bottom: 0.15rem !important;
        }}

        [data-testid="stMain"] [data-testid="stCaptionContainer"] p {{
            color: #94A3B8 !important;
            font-size: 12.5px !important;
            margin-bottom: 0.75rem !important;
        }}

        /* Karty w stylu NASA Mission Control (jak w overview) */
        .st-key-plots_controls_card,
        .st-key-plots_chart_card {{
            background-color: #111625 !important;
            border: 1px solid #1E293B !important;
            border-top: 3px solid {NASA_BLUE} !important;
            border-radius: 8px !important;
            padding: 16px 20px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
        }}

        .st-key-plots_chart_card {{
            padding-bottom: 10px !important;
        }}

        /* Etykiety nad selektorami */
        .nasa-control-label {{
            font-size: 10.5px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748B;
            margin-bottom: 6px;
        }}

        /* Wyrównanie obu selektorów na identycznej wysokości */
        .st-key-plots_controls_card [data-testid="stHorizontalBlock"] {{
            align-items: end !important;
        }}

        .st-key-plots_controls_card [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        .st-key-plots_controls_card [data-testid="stPopover"] > button {{
            background-color: #080B10 !important;
            border: 1px solid #1E293B !important;
            border-radius: 6px !important;
            color: #F8FAFC !important;
            min-height: 42px !important;
            height: 42px !important;
            width: 100% !important;
            box-sizing: border-box !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            transition: border-color 0.2s ease !important;
        }}

        .st-key-plots_controls_card [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
        .st-key-plots_controls_card [data-testid="stPopover"] > button:hover {{
            border-color: #60A5FA !important;
        }}

        .st-key-plots_controls_card [data-testid="stSelectbox"] svg,
        .st-key-plots_controls_card [data-testid="stPopover"] svg {{
            fill: #94A3B8 !important;
            color: #94A3B8 !important;
        }}

        .st-key-plots_controls_card [data-testid="stPopover"] > button {{
            justify-content: space-between !important;
            padding: 0 14px !important;
        }}

        /* Rozwijane menu selectboxa i okno popovera */
        [data-baseweb="popover"] > div,
        [data-baseweb="menu"],
        [data-testid="stPopoverBody"] {{
            background-color: #111625 !important;
            border: 1px solid #1E293B !important;
            border-radius: 6px !important;
            color: #F8FAFC !important;
        }}

        [data-baseweb="menu"] li {{
            background-color: #111625 !important;
            color: #CBD5E1 !important;
        }}

        [data-baseweb="menu"] li:hover,
        [data-baseweb="menu"] li[aria-selected="true"] {{
            background-color: #080B10 !important;
            color: #FFFFFF !important;
        }}

        /* Checkboxy astronautów w kolorze NASA Red */
        .st-key-plots_crew [data-testid="stCheckbox"] label p {{
            color: #F8FAFC !important;
            font-size: 13.5px !important;
        }}

        .st-key-plots_crew [data-testid="stCheckbox"]
            label[data-selected]:not([data-disabled]) > div:has(> svg),
        .st-key-plots_crew [data-testid="stCheckbox"]
            label[data-baseweb="checkbox"]:has(input:checked:not(:disabled))
            > div:first-child {{
            background-color: {NASA_RED} !important;
            border-color: {NASA_RED} !important;
        }}
        </style>
    """)

    try:
        data = load_database_measurements(DEFAULT_DB)
    except (OSError, ValueError, sqlite3.Error, pd.errors.DatabaseError) as error:
        st.error(f"Could not load measurements from {DEFAULT_DB.name}. {error}")
        return

    if data.empty:
        st.info("No measurements available.")
        return

    astronaut_names = (
        data[["astronaut_id", "astronaut_name"]]
        .drop_duplicates(subset="astronaut_id")
        .set_index("astronaut_id")["astronaut_name"]
        .to_dict()
    )
    active_id = _resolve_active_astronaut_id(astronaut, astronaut_names)

    # Pokaż tylko te pozycje menu, dla których istnieją dane w aktualnej bazie.
    available_metric_codes = set(data["metric_code"].unique())
    available_parameters = {
        name: definition
        for name, definition in PARAMETERS.items()
        if any(code in available_metric_codes for code, _ in definition[1])
    }

    if not available_parameters:
        st.info("No supported measurement types were found in the database.")
        return

    with st.container(key="plots_controls_card"):
        parameter_control, crew_control = st.columns(2, gap="medium")

        with parameter_control:
            st.markdown(
                '<div class="nasa-control-label">Parameter</div>',
                unsafe_allow_html=True,
            )
            parameter = st.selectbox(
                "Parameter",
                list(available_parameters),
                key="astronaut_health_parameter_v2",
                label_visibility="collapsed",
            )

        selected_astronauts = []
        with crew_control:
            st.markdown(
                '<div class="nasa-control-label">Compare To</div>',
                unsafe_allow_html=True,
            )
            with st.popover("Astronauts", use_container_width=True):
                with st.container(key="plots_crew"):
                    for astronaut_id, name in astronaut_names.items():
                        if st.checkbox(
                            name,
                            value=True,
                            key=f"plots_crew_{astronaut_id}",
                        ):
                            selected_astronauts.append(astronaut_id)

    if not selected_astronauts:
        st.info("Select at least one astronaut to display the chart.")
        return

    unit, series = available_parameters[parameter]
    palette = qualitative.Alphabet
    colors = {
        astronaut_id: palette[index % len(palette)]
        for index, astronaut_id in enumerate(astronaut_names)
    }

    figure = go.Figure()

    for astronaut_id in selected_astronauts:
        name = astronaut_names[astronaut_id]
        astronaut_measurements = data.loc[data["astronaut_id"] == astronaut_id]

        for index, (metric_code, label) in enumerate(series):
            observations = astronaut_measurements.loc[
                astronaut_measurements["metric_code"] == metric_code
            ].sort_values("measured_at")

            if observations.empty:
                continue

            # Dla pomiaru jednorazowego rysujemy wyłącznie punkt.
            # Dzięki temu np. wzrost lub bazowe wyniki krwi nie są łączone linią.
            display_mode = "lines+markers" if len(observations) > 1 else "markers"
            line_shape = "hv" if metric_code in BINARY_AXIS_LABELS else "linear"

            figure.add_scatter(
                x=observations["measured_at"].tolist(),
                y=observations["value"].tolist(),
                name=f"{name} · {label}" if len(series) > 1 else name,
                mode=display_mode,
                line={
                    "color": colors[astronaut_id],
                    "dash": "solid" if index == 0 else "dash",
                    "width": 4 if astronaut_id == active_id else 2,
                    "shape": line_shape,
                },
                marker={
                    "size": 7 if astronaut_id == active_id else 6,
                    "color": colors[astronaut_id],
                },
                hovertemplate=f"%{{y:.2f}} {unit}<extra>%{{fullData.name}}</extra>",
            )

    if not figure.data:
        st.info("No measurements for the selected parameter and crew.")
        return

    yaxis_options = {
        "title": {"text": unit, "font": {"size": 12, "color": "#94A3B8"}},
        "gridcolor": "#1E293B",
        "linecolor": "#1E293B",
        "zerolinecolor": "#1E293B",
        "tickfont": {"color": "#64748B", "size": 11},
    }

    # Opisowe etykiety dla parametrów binarnych (0/1).
    binary_code = series[0][0] if len(series) == 1 else None
    if binary_code in BINARY_AXIS_LABELS:
        yaxis_options.update(
            {
                "tickmode": "array",
                "tickvals": [0, 1],
                "ticktext": [
                    BINARY_AXIS_LABELS[binary_code][0],
                    BINARY_AXIS_LABELS[binary_code][1],
                ],
                "range": [-0.15, 1.15],
            }
        )

    figure.update_layout(
        title={
            "text": parameter.upper(),
            "font": {"size": 12.5, "color": "#94A3B8"},
            "x": 0,
            "xanchor": "left",
        },
        paper_bgcolor="#111625",
        plot_bgcolor="#080B10",
        font={"color": "#CBD5E1"},
        xaxis={
            "title": {"text": "Mission time", "font": {"size": 12, "color": "#94A3B8"}},
            "hoverformat": "%Y-%m-%d %H:%M",
            "gridcolor": "#1E293B",
            "linecolor": "#1E293B",
            "zerolinecolor": "#1E293B",
            "tickfont": {"color": "#64748B", "size": 11},
        },
        yaxis=yaxis_options,
        hovermode="x unified",
        hoverlabel={
            "bgcolor": "#080B10",
            "bordercolor": NASA_BLUE,
            "font": {"color": "#F8FAFC", "size": 12},
        },
        legend={
            "orientation": "h",
            "y": -0.24,
            "font": {"color": "#CBD5E1", "size": 12},
            "bgcolor": "rgba(0,0,0,0)",
        },
        margin={"t": 44, "r": 16, "l": 52, "b": 96},
    )

    with st.container(key="plots_chart_card"):
        st.plotly_chart(
            figure,
            key="astronaut_health_chart",
            use_container_width=True,
        )
