"""Streamlit charts for astronaut health telemetry."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.colors import qualitative


DEFAULT_DB = Path(__file__).with_name("astronaut_health_demo.db")
NASA_RED = "#E4002B"

# Each entry defines the axis unit and the series for one chart.
PARAMETERS = {
    "Blood pressure": (
        "mmHg",
        (("systolic_mmhg", "Systolic"), ("diastolic_mmhg", "Diastolic")),
    ),
    "Blood oxygen saturation (SpO₂)": ("%", (("spo2_pct", "SpO₂"),)),
    "Blood glucose": ("mg/dL", (("glucose_mg_dl", "Blood glucose"),)),
    "Body temperature": ("°C", (("temperature_c", "Body temperature"),)),
    "Heart rate": ("bpm", (("heart_rate_bpm", "Heart rate"),)),
    "Heart rate variability (HRV)": ("ms", (("hrv_rmssd_ms", "RMSSD"),)),
    "Sleep duration": ("h", (("sleep_hours", "Sleep duration"),)),
    "Hydration (fluid intake)": ("L/day", (("fluid_intake_l", "Fluid intake"),)),
}


def load_database_measurements(database_path: str | Path) -> pd.DataFrame:
    """Read observations, including dates from older daily demo databases."""
    database_uri = Path(database_path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(database_uri, uri=True)) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(measurements)")}
        time_column = "measured_at" if "measured_at" in columns else "date"
        readings = pd.read_sql_query(
            f"SELECT astronaut_id, {time_column} AS measured_at, metric_code, value "
            "FROM measurements ORDER BY astronaut_id, metric_code, measured_at",
            connection,
        )

    readings["measured_at"] = pd.to_datetime(readings["measured_at"], format="ISO8601")
    return readings


def render_health_charts(
    database_path: str | Path = DEFAULT_DB,
    *,
    key_prefix: str = "astronaut_health",
    demo: bool = True,
) -> None:
    """Render telemetry charts inside an existing Streamlit page."""
    st.header("Astronaut health trends")
    if demo:
        st.caption("Synthetic demo data · Daily fluid intake is shown as a hydration proxy.")

    try:
        data = load_database_measurements(database_path)
    except (OSError, ValueError, sqlite3.Error, pd.errors.DatabaseError) as error:
        st.error(f"Could not load measurements. {error}")
        return

    if data.empty:
        st.info("No measurements available.")
        return

    astronauts = data["astronaut_id"].unique().tolist()
    parameter_control, crew_control = st.columns(2)
    parameter = parameter_control.selectbox(
        "Parameter", list(PARAMETERS), key=f"{key_prefix}_parameter"
    )
    selected_astronauts = []
    with crew_control.popover("Astronauts"):
        st.html(f"""
            <style>
            [class*="st-key-crew_checkbox_colors_"] [data-testid="stCheckbox"]
                label[data-selected]:not([data-disabled]) > div:has(> svg),
            [class*="st-key-crew_checkbox_colors_"] [data-testid="stCheckbox"]
                label[data-baseweb="checkbox"]:has(input:checked:not(:disabled))
                > div:first-child {{
                background-color: {NASA_RED} !important;
                border-color: {NASA_RED} !important;
            }}
            </style>
        """)
        with st.container(key=f"crew_checkbox_colors_{key_prefix}"):
            for person in astronauts:
                if st.checkbox(person, value=True, key=f"{key_prefix}_crew_{person}"):
                    selected_astronauts.append(person)

    if not selected_astronauts:
        st.info("Select at least one astronaut to display the chart.")
        return

    unit, series = PARAMETERS[parameter]
    figure = go.Figure()
    palette = qualitative.Alphabet
    colors = {
        person: palette[index % len(palette)]
        for index, person in enumerate(astronauts)
    }
    for person in selected_astronauts:
        measurements = data.loc[data["astronaut_id"] == person]
        for index, (column, label) in enumerate(series):
            observations = measurements.loc[measurements["metric_code"] == column]
            if observations.empty:
                continue
            figure.add_scatter(
                x=observations["measured_at"].tolist(),
                y=observations["value"].tolist(),
                name=f"{person} · {label}" if len(series) > 1 else person,
                mode="lines+markers",
                line={
                    "color": colors[person],
                    "dash": "solid" if index == 0 else "dash",
                },
                connectgaps=False,
                hovertemplate=f"%{{y:.2f}} {unit}",
            )

    if not figure.data:
        st.info("No measurements for the selected parameter and crew.")
        return

    figure.update_layout(
        title=parameter,
        xaxis={"title": "Mission time", "hoverformat": "%Y-%m-%d %H:%M"},
        yaxis_title=unit,
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.24},
        margin={"b": 96},
    )
    st.plotly_chart(figure, key=f"{key_prefix}_chart")


if __name__ == "__main__":
    render_health_charts()
