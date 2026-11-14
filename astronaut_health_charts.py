"""Streamlit charts for astronaut health telemetry."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.colors import qualitative


DEFAULT_CSV = Path(__file__).with_name("astronaut_health_demo.csv")

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


def load_measurements(csv_path: str | Path) -> pd.DataFrame:
    """Read one row per astronaut and measurement date."""
    data = pd.read_csv(csv_path, dtype={"astronaut_id": "string"})
    measurement_columns = [
        column for _, series in PARAMETERS.values() for column, _ in series
    ]
    missing = {"astronaut_id", "date", *measurement_columns} - set(data.columns)
    if missing:
        raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}.")

    data["astronaut_id"] = data["astronaut_id"].str.strip()
    data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d")
    if (
        data[["astronaut_id", "date"]].isna().any().any()
        or data["astronaut_id"].eq("").any()
    ):
        raise ValueError("Every measurement needs an astronaut ID and a date.")
    if data.duplicated(["astronaut_id", "date"]).any():
        raise ValueError("Use one row per astronaut and date.")

    for column in measurement_columns:
        data[column] = pd.to_numeric(data[column], errors="raise")

    return data.sort_values(["astronaut_id", "date"])


def render_health_charts(
    csv_path: str | Path = DEFAULT_CSV,
    *,
    key_prefix: str = "astronaut_health",
    demo: bool = True,
) -> None:
    """Render telemetry charts inside an existing Streamlit page."""
    st.header("Astronaut health trends")
    if demo:
        st.caption("Synthetic demo data · Daily fluid intake is shown as a hydration proxy.")

    try:
        data = load_measurements(csv_path)
    except (OSError, ValueError) as error:
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
        measurements = data.loc[data["astronaut_id"] == person].set_index("date")
        # Preserve gaps when a day's row or an individual measurement is missing.
        dates = pd.date_range(measurements.index.min(), measurements.index.max(), freq="D")
        measurements = measurements.reindex(dates)
        for index, (column, label) in enumerate(series):
            values = measurements[column]
            if values.isna().all():
                continue
            figure.add_scatter(
                x=measurements.index.to_pydatetime(),
                y=values.tolist(),
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
        xaxis_title="Date",
        yaxis_title=unit,
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.24},
        margin={"b": 96},
    )
    st.plotly_chart(figure, key=f"{key_prefix}_chart")


if __name__ == "__main__":
    render_health_charts()
