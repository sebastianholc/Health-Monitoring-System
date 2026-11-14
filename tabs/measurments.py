import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st

DB_PATH = Path(__file__).resolve().parents[1] / "astronaut_health_demo_30d.db"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
SHARED_METRICS = {
    "heart_rate_bpm", "spo2_pct", "temperature_c",
}


def open_database():
    connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=rw", uri=True)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with closing(open_database()) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_markers (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                astronaut_id TEXT NOT NULL REFERENCES information(astronaut_id),
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                source TEXT NOT NULL,
                UNIQUE (astronaut_id, metric, timestamp)
            )
        """)


def insert_markers(astronaut_id, records, timestamp):
    rows = [(timestamp, astronaut_id, metric, float(value)) for metric, value in records]
    with closing(open_database()) as connection, connection:
        connection.executemany("""
            INSERT INTO telemetry_markers (timestamp, astronaut_id, metric, value, source)
            VALUES (?, ?, ?, ?, 'manual')
        """, rows)
        connection.executemany("""
            INSERT INTO measurements (measured_at, astronaut_id, metric_code, value)
            VALUES (?, ?, ?, ?)
        """, [row for row in rows if row[2] in SHARED_METRICS])
    return len(rows)


def render_manual_telemetry(astronaut_id):
    st.subheader("Telemetria")
    with st.form(f"manual_markers_form_{astronaut_id}"):
        readings = {
            "heart_rate_bpm": st.number_input(
                "Tętno [bpm]", min_value=30.0, max_value=240.0, value=None, step=1.0,
            ),
            "spo2_pct": st.number_input(
                "SpO₂ [%]", min_value=70.0, max_value=100.0, value=None, step=0.5,
            ),
            "temperature_c": st.number_input(
                "Temperatura [°C]", min_value=34.0, max_value=42.0, value=None, step=0.1,
            ),
        }
        submitted = st.form_submit_button("Zapisz pomiary")

    if not submitted:
        return

    records = [(metric, value) for metric, value in readings.items() if value is not None]
    if not records:
        st.warning("Wpisz co najmniej jeden pomiar.")
        return

    timestamp = datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)
    try:
        init_db()
        saved_count = insert_markers(astronaut_id, records, timestamp)
    except sqlite3.IntegrityError:
        st.error("Zapis odrzucony. Sprawdź ID astronauty i czy te metryki mają już pomiar w tej minucie.")
    except sqlite3.Error as error:
        st.error(f"Nie udało się zapisać pomiarów: {error}")
    else:
        st.success(f"Zapisano {saved_count} pomiarów o {timestamp} UTC.")


def render_face_scan(astronaut_id):
    st.subheader("Skan twarzy · demo")
    model_path = DB_PATH.with_name("face_landmarker.task")
    if not model_path.is_file():
        st.warning(f"Brakuje pliku modelu. Zapisz go tutaj: {model_path}")
        return

    if not st.button("Uruchom skan kamery", key=f"face_scan_{astronaut_id}"):
        return

    try:
        from face_diagnostics import run_face_scan
    except ImportError as error:
        st.warning(f"Moduł kamery jest niedostępny: {error}")
        return

    result = run_face_scan()
    if result is not None:
        st.write({
            "Średni EAR": result["mean_ear"],
            "Klatki z zamkniętymi oczami [%]": result["perclos"],
            "Odchylenie proporcji twarzy od wzorca [%]": result["fluid_shift_pct"],
        })
        st.caption("Wskaźniki eksperymentalne z obrazu kamery.")


def measurments(astronaut_data):
    from games import cognitive_games_section

    astronaut_id = getattr(astronaut_data, "id", None)
    if not astronaut_id:
        st.warning("Wybierz astronautę z identyfikatorem w bazie.")
        return

    top_left, top_right = st.columns(2, gap="large")
    with top_left:
        telemetry_panel = st.container(border=True)
    with top_right:
        game_panel = st.container(border=True)

    bottom_left, bottom_right = st.columns(2, gap="large")
    with bottom_left:
        face_panel = st.container(border=True)
    with bottom_right:
        ranking_panel = st.container(border=True)

    with telemetry_panel:
        render_manual_telemetry(astronaut_id)
    with face_panel:
        render_face_scan(astronaut_id)
    with game_panel:
        cognitive_games_section(astronaut_data, ranking_panel=ranking_panel)
