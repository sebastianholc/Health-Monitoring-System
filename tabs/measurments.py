import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import streamlit as st

DB_PATH = Path(__file__).resolve().parents[1] / "astronaut_health_demo_30d.db"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
SHARED_METRICS = {
    "heart_rate_bpm",
    "spo2_pct",
    "temperature_c",
    "fluid_intake_l",
    "body_mass_kg",
    "psych_wellbeing_score",
}
NASA_BLUE = "#0032A0"
NASA_RED = "#E4002B"


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
    st.markdown(
        '<div class="nasa-card-header">'
        '<span class="nasa-card-title">Manual Telemetry</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form(f"manual_markers_form_{astronaut_id}"):
        inputs_col, action_col = st.columns([1.2, 1], gap="medium")

        with inputs_col:
            fluid_val = st.number_input(
                "Fluid Intake [L]", min_value=0.0, max_value=10.0, value=None, step=0.1,
            )
            mass_val = st.number_input(
                "Body Mass [kg]", min_value=40.0, max_value=150.0, value=None, step=0.1,
            )
            wellbeing_val = st.number_input(
                "Wellbeing Score [/100]", min_value=0.0, max_value=100.0, value=None, step=1.0,
            )

        with action_col:
            submitted = st.form_submit_button("Log Entry")

        readings = {
            "fluid_intake_l": fluid_val,
            "body_mass_kg": mass_val,
            "psych_wellbeing_score": wellbeing_val,
        }

    if not submitted:
        return

    records = [(metric, value) for metric, value in readings.items() if value is not None]
    if not records:
        st.toast("Enter at least one measurement value before logging.")
        return

    timestamp = datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)
    try:
        init_db()
        saved_count = insert_markers(astronaut_id, records, timestamp)
    except sqlite3.IntegrityError:
        st.toast("Entry rejected: duplicate metric logged within the same UTC minute.")
    except sqlite3.Error as error:
        st.toast(f"Database error: {error}")
    else:
        st.toast(f"Logged {saved_count} manual entry(s) at {timestamp} UTC.")


def render_face_scan(astronaut_id):
    st.markdown(
        '<div class="nasa-card-header">'
        '<span class="nasa-card-title">Optical Face Scan</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    model_path = DB_PATH.with_name("face_landmarker.task")
    if not model_path.is_file():
        st.warning(f"Model file missing. Place face_landmarker.task at: {model_path}")
        return

    result_key = f"face_scan_result_{astronaut_id}"
    last_result = st.session_state.get(result_key)

    left_col, right_col = st.columns([1.25, 1], gap="medium")

    with left_col:
        if last_result is not None:
            ear_val = escape(str(last_result["mean_ear"]))
            perclos_val = f'{escape(str(last_result["perclos"]))}<span class="nasa-kpi-unit">%</span>'
            fluid_val = f'{escape(str(last_result["fluid_shift_pct"]))}<span class="nasa-kpi-unit">%</span>'

            st.markdown(
                f'<div class="nasa-kpi-stack">'
                f'<div class="nasa-kpi-row">'
                f'<span class="nasa-kpi-label">Mean EAR</span>'
                f'<span class="nasa-kpi-value">{ear_val}</span>'
                f'</div>'
                f'<div class="nasa-kpi-row">'
                f'<span class="nasa-kpi-label">PERCLOS</span>'
                f'<span class="nasa-kpi-value">{perclos_val}</span>'
                f'</div>'
                f'<div class="nasa-kpi-row">'
                f'<span class="nasa-kpi-label">Fluid Shift</span>'
                f'<span class="nasa-kpi-value">{fluid_val}</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="nasa-sub-box nasa-face-desc">'
                '<div class="nasa-status-heading">5-SEC BIOMETRIC CAPTURE</div>'
                '<p class="nasa-note">Analyzes ocular fatigue (EAR &amp; PERCLOS) and cephalad fluid shift ratio using optical facial landmarks.</p>'
                '</div>',
                unsafe_allow_html=True,
            )

        start_clicked = st.button("Start Scan", key=f"face_scan_{astronaut_id}", use_container_width=True)

    with right_col:
        camera_slot = st.empty()
        camera_slot.markdown(
            '<div class="nasa-camera-standby">'
            '<div class="cam-reticle"></div>'
            '<div class="cam-standby-text">OPTICAL SENSOR<br>STANDBY</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    if not start_clicked:
        return

    try:
        from face_diagnostics import run_face_scan
    except ImportError as error:
        st.toast(f"Camera module unavailable: {error}")
        return

    result = run_face_scan(video_slot=camera_slot)
    if result is not None:
        st.session_state[result_key] = result
        st.rerun()


def measurments(astronaut_data):
    from games import cognitive_games_section

    measurements_css = f"""
<style>
[data-testid="stMainBlockContainer"] {{
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
}}

[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child:has(style) {{
    display: none !important;
}}

[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div {{
    padding-top: 0 !important;
}}

/* Neutralizacja dziedziczonych odstępów z HMS_app.py wewnątrz kolumn i kart */
[data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] [data-testid="stVerticalBlock"] > div,
[data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] [data-testid="stVerticalBlock"] > div:first-child,
[data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] [data-testid="stVerticalBlock"] > div:nth-child(2),
[data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] [data-testid="stVerticalBlock"] > div:nth-child(3) {{
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-top: 0 !important;
}}

/* 4 równe karty po 1/4 ekranu (siatka 2x2) — wygląd identyczny jak .nasa-card w overview */
.st-key-meas_telemetry_card,
.st-key-meas_games_card,
.st-key-meas_face_card,
.st-key-meas_ranking_card {{
    background-color: #111625 !important;
    border: 1px solid #1E293B !important;
    border-top: 3px solid {NASA_BLUE} !important;
    border-radius: 8px !important;
    padding: 18px !important;
    margin: 0 !important;
    width: 100% !important;
    height: 350px !important;
    min-height: 350px !important;
    max-height: 350px !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
}}

.st-key-meas_telemetry_card > [data-testid="stVerticalBlock"],
.st-key-meas_games_card > [data-testid="stVerticalBlock"],
.st-key-meas_face_card > [data-testid="stVerticalBlock"],
.st-key-meas_ranking_card > [data-testid="stVerticalBlock"] {{
    gap: 0 !important;
    width: 100% !important;
}}

/* Nagłówki kart identyczne jak w overview */
.nasa-card-header {{
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    margin: 0 0 18px 0 !important;
    padding: 0 0 8px 0 !important;
    border-bottom: 1px solid #1E293B !important;
    width: 100% !important;
    height: 26px !important;
    min-height: 26px !important;
    box-sizing: border-box !important;
}}

.nasa-card-title {{
    font-size: 11.5px !important;
    font-weight: 700 !important;
    letter-spacing: 1.8px !important;
    line-height: 1.4 !important;
    text-transform: uppercase !important;
    color: #94A3B8 !important;
    margin: 0 !important;
}}

/* Wewnętrzne kontenery informacyjne */
.nasa-sub-box {{
    background-color: #080B10 !important;
    border: 1px solid #1E293B !important;
    border-left: 3px solid {NASA_BLUE} !important;
    border-radius: 6px !important;
    padding: 18px !important;
    box-sizing: border-box !important;
}}

.nasa-status-heading {{
    font-size: 10.5px !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    color: #CBD5E1 !important;
    margin-bottom: 8px !important;
}}

.nasa-note,
.nasa-sub-box p {{
    font-size: 22px !important;
    color: #94A3B8 !important;
    line-height: 1.45 !important;
    margin: 0 !important;
}}

/* ==========================================
   1. MANUAL TELEMETRY — większy kwadratowy przycisk Log Entry (188x188 px) na środku
   ========================================== */
.st-key-meas_telemetry_card [data-testid="stForm"] {{
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
}}

.st-key-meas_telemetry_card [data-testid="stForm"] [data-testid="stHorizontalBlock"] {{
    gap: 18px !important;
    align-items: center !important;
    height: 270px !important;
    margin: 0 !important;
}}

.st-key-meas_telemetry_card [data-testid="stForm"] [data-testid="stColumn"]:first-child {{
    flex: 1.2 1 0 !important;
    width: auto !important;
    min-width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}}

.st-key-meas_telemetry_card [data-testid="stForm"] [data-testid="stColumn"]:last-child {{
    flex: 1 1 0 !important;
    width: auto !important;
    min-width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}}

.st-key-meas_telemetry_card [data-testid="stForm"] [data-testid="stColumn"]:first-child > [data-testid="stVerticalBlock"] {{
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    height: 270px !important;
    gap: 18px !important;
}}

.st-key-meas_telemetry_card [data-testid="stForm"] [data-testid="stColumn"]:last-child > [data-testid="stVerticalBlock"] {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 270px !important;
    gap: 0 !important;
}}

.st-key-meas_telemetry_card [data-testid="stNumberInput"] {{
    margin: 0 !important;
    padding: 0 !important;
    height: 78px !important;
}}

.st-key-meas_telemetry_card [data-testid="stNumberInput"] label {{
    min-height: 0 !important;
    margin-bottom: 6px !important;
    padding: 0 !important;
}}

.st-key-meas_telemetry_card [data-testid="stNumberInput"] label p {{
    font-size: 10.5px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    color: #64748B !important;
    line-height: 1.2 !important;
}}

.st-key-meas_telemetry_card [data-testid="stNumberInput"] div[data-baseweb="input"] {{
    background-color: #080B10 !important;
    border: 1px solid #1E293B !important;
    border-radius: 6px !important;
    color: #F8FAFC !important;
    min-height: 52px !important;
    height: 52px !important;
}}

.st-key-meas_telemetry_card [data-testid="stNumberInput"] input {{
    color: #F8FAFC !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    padding: 0 12px !important;
}}

.st-key-meas_telemetry_card [data-testid="stNumberInput"] button {{
    background-color: #111625 !important;
    border-left: 1px solid #1E293B !important;
    color: #94A3B8 !important;
    min-height: 50px !important;
    height: 50px !important;
}}

.st-key-meas_telemetry_card [data-testid="stFormSubmitButton"] {{
    margin: 0 !important;
    padding: 0 !important;
    width: 188px !important;
    height: 188px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}

.st-key-meas_telemetry_card [data-testid="stFormSubmitButton"] button {{
    background-color: {NASA_BLUE} !important;
    border: 1px solid #1D4ED8 !important;
    color: #F8FAFC !important;
    border-radius: 6px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: 1.3px !important;
    text-transform: uppercase !important;
    width: 188px !important;
    min-width: 188px !important;
    max-width: 188px !important;
    height: 188px !important;
    min-height: 188px !important;
    margin: 0 !important;
    transition: all 0.15s ease !important;
}}

.st-key-meas_telemetry_card [data-testid="stFormSubmitButton"] button:hover {{
    background-color: #0041CC !important;
    border-color: #60A5FA !important;
    color: #FFFFFF !important;
}}

/* ==========================================
   2. COGNITIVE GAME // DOCKING SIM — przycisk 188x188 px + opis dopasowany do tekstu
   ========================================== */
.st-key-meas_games_card [data-testid="stHorizontalBlock"] {{
    gap: 18px !important;
    align-items: center !important;
    margin: 0 !important;
}}

.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_start),
.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_retry) {{
    height: 270px !important;
}}

.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_start) > [data-testid="stColumn"]:first-child,
.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_retry) > [data-testid="stColumn"]:first-child {{
    flex: 0 0 188px !important;
    width: 188px !important;
    min-width: 188px !important;
    max-width: 188px !important;
    padding: 0 !important;
}}

.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_start) > [data-testid="stColumn"]:first-child > [data-testid="stVerticalBlock"],
.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_retry) > [data-testid="stColumn"]:first-child > [data-testid="stVerticalBlock"] {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 270px !important;
    gap: 0 !important;
}}

.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_start) > [data-testid="stColumn"]:last-child,
.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_retry) > [data-testid="stColumn"]:last-child {{
    flex: 1 1 0 !important;
    width: auto !important;
    min-width: 0 !important;
    padding: 0 !important;
}}

.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_start) > [data-testid="stColumn"]:last-child > [data-testid="stVerticalBlock"],
.st-key-meas_games_card [data-testid="stHorizontalBlock"]:has(.st-key-do_retry) > [data-testid="stColumn"]:last-child > [data-testid="stVerticalBlock"] {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 270px !important;
    gap: 0 !important;
}}

.st-key-meas_games_card .st-key-do_start,
.st-key-meas_games_card .st-key-do_retry {{
    width: 188px !important;
    height: 188px !important;
    margin: 0 !important;
}}

.st-key-meas_games_card .st-key-do_start button,
.st-key-meas_games_card .st-key-do_retry button {{
    background-color: {NASA_BLUE} !important;
    border: 1px solid #1D4ED8 !important;
    color: #F8FAFC !important;
    border-radius: 6px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: 1.3px !important;
    text-transform: uppercase !important;
    width: 188px !important;
    min-width: 188px !important;
    max-width: 188px !important;
    height: 188px !important;
    min-height: 188px !important;
    margin: 0 !important;
    transition: all 0.15s ease !important;
}}

.st-key-meas_games_card .st-key-do_start button:hover,
.st-key-meas_games_card .st-key-do_retry button:hover {{
    background-color: #0041CC !important;
    border-color: #60A5FA !important;
    color: #FFFFFF !important;
}}

.nasa-game-desc {{
    width: 100% !important;
    height: fit-content !important;
    padding: 16px 18px !important;
    margin: 0 !important;
}}

/* Przyciski Capture / Ignore w trakcie rundy */
.st-key-meas_games_card .st-key-do_cap button,
.st-key-meas_games_card .st-key-do_pass button {{
    background-color: #080B10 !important;
    border: 1px solid #1E293B !important;
    color: #F8FAFC !important;
    border-radius: 6px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    min-height: 174px !important;
    height: 174px !important;
    width: 100% !important;
    margin: 0 !important;
    transition: all 0.15s ease !important;
}}

.st-key-meas_games_card .st-key-do_cap button:hover {{
    background-color: rgba(16, 185, 129, 0.14) !important;
    border-color: #10B981 !important;
    color: #10B981 !important;
}}

.st-key-meas_games_card .st-key-do_pass button:hover {{
    background-color: rgba(0, 50, 160, 0.25) !important;
    border-color: #60A5FA !important;
    color: #FFFFFF !important;
}}

/* ==========================================
   3. OPTICAL FACE SCAN — bez zmian
   ========================================== */
.st-key-meas_face_card [data-testid="stHorizontalBlock"] {{
    gap: 18px !important;
    align-items: stretch !important;
    height: 270px !important;
    margin: 0 !important;
}}

.st-key-meas_face_card [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {{
    flex: 1 1 0 !important;
    width: auto !important;
    min-width: 0 !important;
    padding: 0 !important;
}}

.st-key-meas_face_card [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {{
    flex: 0 0 270px !important;
    width: 270px !important;
    min-width: 270px !important;
    max-width: 270px !important;
    padding: 0 !important;
}}

.st-key-meas_face_card [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child > [data-testid="stVerticalBlock"] {{
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    height: 270px !important;
    gap: 18px !important;
}}

.nasa-face-desc {{
    height: 174px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    margin: 0 !important;
}}

.nasa-kpi-stack {{
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    height: 174px !important;
    gap: 12px !important;
    margin: 0 !important;
}}

.nasa-kpi-row {{
    background-color: #080B10 !important;
    border: 1px solid #1E293B !important;
    border-radius: 6px !important;
    padding: 0 14px !important;
    height: 50px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    box-sizing: border-box !important;
}}

.nasa-kpi-label {{
    font-size: 10.5px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    color: #64748B !important;
}}

.nasa-kpi-value {{
    font-size: 17px !important;
    font-weight: 700 !important;
    color: #F8FAFC !important;
}}

.nasa-kpi-unit {{
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #94A3B8 !important;
    margin-left: 3px !important;
}}

.st-key-meas_face_card button {{
    background-color: {NASA_BLUE} !important;
    border: 1px solid #1D4ED8 !important;
    color: #F8FAFC !important;
    border-radius: 6px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    min-height: 78px !important;
    height: 78px !important;
    width: 100% !important;
    margin: 0 !important;
    transition: all 0.15s ease !important;
}}

.st-key-meas_face_card button:hover {{
    background-color: #0041CC !important;
    border-color: #60A5FA !important;
    color: #FFFFFF !important;
}}

.nasa-camera-standby {{
    width: 270px !important;
    height: 270px !important;
    background-color: #080B10 !important;
    border: 1px solid #1E293B !important;
    border-radius: 6px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
}}

.cam-reticle {{
    width: 48px !important;
    height: 48px !important;
    border: 1.5px dashed #334155 !important;
    border-radius: 50% !important;
    margin-bottom: 12px !important;
}}

.cam-standby-text {{
    font-size: 10.5px !important;
    font-weight: 700 !important;
    letter-spacing: 1.4px !important;
    text-align: center !important;
    color: #64748B !important;
    line-height: 1.4 !important;
}}

.st-key-meas_face_card [data-testid="stImage"] {{
    display: flex !important;
    justify-content: center !important;
    margin: 0 !important;
}}

.st-key-meas_face_card [data-testid="stImage"] img {{
    width: 270px !important;
    height: 270px !important;
    max-width: 270px !important;
    max-height: 270px !important;
    object-fit: cover !important;
    border-radius: 6px !important;
    border: 1px solid #1E293B !important;
}}

/* ==========================================
   4. CREW LEADERBOARD — bez zmian
   ========================================== */
.nasa-lb-wrap {{
    height: 270px !important;
    overflow-y: auto !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    scrollbar-width: thin !important;
    scrollbar-color: #475569 #111625 !important;
}}

.nasa-lb-head {{
    display: grid !important;
    grid-template-columns: 1.4fr 0.9fr 0.6fr 1.3fr !important;
    gap: 10px !important;
    padding: 0 12px 4px 12px !important;
    font-size: 10.5px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    color: #64748B !important;
}}

.nasa-lb-row {{
    display: grid !important;
    grid-template-columns: 1.4fr 0.9fr 0.6fr 1.3fr !important;
    gap: 10px !important;
    align-items: center !important;
    background-color: #080B10 !important;
    border: 1px solid #1E293B !important;
    border-radius: 6px !important;
    padding: 10px 12px !important;
}}

.nasa-lb-name {{
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #F8FAFC !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.nasa-lb-stat {{
    font-size: 13.5px !important;
    font-weight: 600 !important;
    color: #CBD5E1 !important;
}}

.nasa-lb-acc-cell {{
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}}

.nasa-lb-track {{
    flex: 1 !important;
    height: 7px !important;
    background-color: #111625 !important;
    border: 1px solid #1E293B !important;
    border-radius: 4px !important;
    overflow: hidden !important;
}}

.nasa-lb-fill {{
    height: 100% !important;
    background-color: {NASA_RED} !important;
    border-radius: 4px !important;
}}

.nasa-lb-acc-text {{
    font-size: 12px !important;
    font-weight: 700 !important;
    color: #F8FAFC !important;
    min-width: 34px !important;
    text-align: right !important;
}}
</style>
"""
    st.markdown(measurements_css, unsafe_allow_html=True)

    astronaut_id = getattr(astronaut_data, "id", None)
    if not astronaut_id:
        st.warning("Select an astronaut with a valid database ID.")
        return

    top_left, top_right = st.columns(2, gap="medium")
    with top_left:
        telemetry_panel = st.container(key="meas_telemetry_card")
    with top_right:
        game_panel = st.container(key="meas_games_card")

    bottom_left, bottom_right = st.columns(2, gap="medium")
    with bottom_left:
        face_panel = st.container(key="meas_face_card")
    with bottom_right:
        ranking_panel = st.container(key="meas_ranking_card")

    with telemetry_panel:
        render_manual_telemetry(astronaut_id)
    with face_panel:
        render_face_scan(astronaut_id)
    with game_panel:
        cognitive_games_section(astronaut_data, ranking_panel=ranking_panel)