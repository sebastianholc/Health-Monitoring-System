import random
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = Path(__file__).resolve().parent / "astronaut_health_demo_30d.db"
GAME_NAME = "Docking Override"


def open_database():
    connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=rw", uri=True)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_games_db():
    with closing(open_database()) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS cognitive_game_scores (
                id INTEGER PRIMARY KEY,
                astronaut_id TEXT NOT NULL REFERENCES information(astronaut_id),
                game_name TEXT NOT NULL,
                reaction_time_ms INTEGER NOT NULL CHECK (reaction_time_ms >= 0),
                success INTEGER NOT NULL CHECK (success IN (0, 1)),
                timestamp TEXT NOT NULL
            )
        """)


def save_game_result(astronaut_id, game_name, reaction_time_ms, success):
    with closing(open_database()) as connection, connection:
        connection.execute("""
            INSERT INTO cognitive_game_scores
                (astronaut_id, game_name, reaction_time_ms, success, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (astronaut_id, game_name, int(reaction_time_ms), int(success),
              datetime.now(timezone.utc).isoformat(timespec="seconds")))


def render_leaderboard(game_name):
    with closing(open_database()) as connection:
        df = pd.read_sql_query("""
            SELECT i.name AS astronaut_name,
                   MIN(CASE WHEN s.success = 1 THEN s.reaction_time_ms END) AS best_time_ms,
                   COUNT(*) AS runs,
                   100.0 * AVG(s.success) AS accuracy_pct
            FROM cognitive_game_scores AS s
            JOIN information AS i ON i.astronaut_id = s.astronaut_id
            WHERE s.game_name = ?
            GROUP BY s.astronaut_id, i.name
            ORDER BY best_time_ms IS NULL, best_time_ms
        """, connection, params=(game_name,))

    if df.empty:
        st.markdown(
            '<div class="nasa-sub-box" style="height: 270px; display: flex; flex-direction: column; justify-content: center;">'
            '<div class="nasa-status-heading">NO SIMULATION RECORDS</div>'
            '<p class="nasa-note">No runs logged yet. Complete a Docking Sim drill in the upper-right card to populate the crew leaderboard.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    rows_html = []
    for _, row in df.iterrows():
        name = escape(str(row["astronaut_name"]))
        best_ms = f"{int(row['best_time_ms'])} ms" if pd.notna(row["best_time_ms"]) else "—"
        runs = int(row["runs"])
        acc = max(0.0, min(100.0, float(row["accuracy_pct"] or 0.0)))

        rows_html.append(
            f'<div class="nasa-lb-row">'
            f'<div class="nasa-lb-name">{name}</div>'
            f'<div class="nasa-lb-stat">{best_ms}</div>'
            f'<div class="nasa-lb-stat">{runs}</div>'
            f'<div class="nasa-lb-acc-cell">'
            f'<div class="nasa-lb-track"><div class="nasa-lb-fill" style="width: {acc:.1f}%;"></div></div>'
            f'<span class="nasa-lb-acc-text">{acc:.0f}%</span>'
            f'</div>'
            f'</div>'
        )

    leaderboard_html = (
        '<div class="nasa-lb-wrap">'
        '<div class="nasa-lb-head">'
        '<span>Astronaut</span>'
        '<span>Best Time</span>'
        '<span>Runs</span>'
        '<span>Accuracy</span>'
        '</div>'
        + "".join(rows_html)
        + '</div>'
    )
    st.markdown(leaderboard_html, unsafe_allow_html=True)


def cognitive_games_section(astronaut, *, ranking_panel=None):
    astronaut_id = getattr(astronaut, "id", None)
    if not astronaut_id:
        st.warning("Select an astronaut with a valid database ID.")
        return

    try:
        init_games_db()
        render_docking_override(astronaut_id)
        if ranking_panel is None:
            render_ranking()
        else:
            with ranking_panel:
                render_ranking()
    except (sqlite3.Error, pd.errors.DatabaseError) as error:
        st.error(f"Failed to read or save simulation scores: {error}")


def render_docking_override(astronaut_id):
    if st.session_state.get("cognitive_game_owner") != astronaut_id:
        for key in list(st.session_state):
            if key.startswith(("di_", "do_", "at_", "cs_")):
                del st.session_state[key]
        st.session_state.cognitive_game_owner = astronaut_id

    st.markdown(
        '<div class="nasa-card-header">'
        '<span class="nasa-card-title">Cognitive Game // Docking Sim</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if "do_state" not in st.session_state:
        st.session_state.do_state = "idle"

    if st.session_state.do_state == "idle":
        btn_col, info_col = st.columns([0.75, 1.25], gap="medium")
        with btn_col:
            if st.button("Arm Airlock", key="do_start"):
                st.session_state.do_state = "waiting"
                st.rerun()
        with info_col:
            st.markdown(
                '<div class="nasa-sub-box nasa-game-desc">'
                '<div class="nasa-status-heading">IMPULSE &amp; REFLEX TEST</div>'
                '<p class="nasa-note" style="margin-bottom: 10px;">'
                'Cognitive reaction drill simulating cargo airlock capture under time pressure.'
                '</p>'
                '<p class="nasa-note" style="margin-bottom: 6px;">'
                '• Tap <strong style="color: #F8FAFC;">Capture</strong> when a <strong style="color: #10B981;">Supply Capsule</strong> approaches.'
                '</p>'
                '<p class="nasa-note">'
                '• Tap <strong style="color: #F8FAFC;">Ignore</strong> on <strong style="color: #CBD5E1;">Micrometeorites</strong> or <strong style="color: #CBD5E1;">Solar Flares</strong>.'
                '</p>'
                '</div>',
                unsafe_allow_html=True,
            )

    elif st.session_state.do_state == "waiting":
        st.markdown(
            '<div style="background-color: #080B10; border: 1px solid #1E293B; border-left: 3px solid #0032A0; '
            'border-radius: 6px; height: 270px; display: flex; flex-direction: column; align-items: center; '
            'justify-content: center; text-align: center; padding: 18px; box-sizing: border-box;">'
            '<div style="font-size: 10.5px; font-weight: 700; letter-spacing: 1.8px; color: #60A5FA; margin-bottom: 8px;">'
            'SIMULATION RADAR ACTIVE</div>'
            '<div style="font-size: 17px; font-weight: 700; color: #F8FAFC;">HOLD STEADY — TARGET APPROACHING...</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        time.sleep(random.uniform(1.0, 3.0))
        st.session_state.do_is_go = random.random() > 0.4
        st.session_state.do_start_time = time.perf_counter()
        st.session_state.do_state = "action"
        st.rerun()

    elif st.session_state.do_state == "action":
        is_go = st.session_state.do_is_go
        label = "SUPPLY CAPSULE" if is_go else random.choice(["MICROMETEORITE", "SOLAR FLARE"])
        sub = "VALID CAPTURE TARGET" if is_go else "HAZARD — DO NOT CAPTURE"
        accent = "#10B981" if is_go else "#F59E0B"

        st.markdown(
            f'<div style="background-color: #080B10; border: 1px solid #1E293B; border-left: 3px solid {accent}; '
            f'border-radius: 6px; padding: 12px 18px; text-align: center; margin-bottom: 18px; height: 78px; '
            f'display: flex; flex-direction: column; justify-content: center; box-sizing: border-box;">'
            f'<div style="font-size: 10px; font-weight: 700; letter-spacing: 1.5px; color: {accent}; margin-bottom: 2px;">{sub}</div>'
            f'<div style="font-size: 19px; font-weight: 700; letter-spacing: 1.2px; color: #F8FAFC;">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2, gap="medium")
        with col1:
            if st.button("Capture", use_container_width=True, key="do_cap"):
                rt = round((time.perf_counter() - st.session_state.do_start_time) * 1000)
                save_game_result(astronaut_id, GAME_NAME, rt, success=is_go)

                if is_go:
                    st.session_state.do_msg = f"Supply capsule secured in {rt} ms."
                    st.session_state.do_rt = f"{rt} ms"
                    st.session_state.do_status = "success"
                else:
                    st.session_state.do_msg = f"False positive: hazard captured ({rt} ms)."
                    st.session_state.do_rt = f"{rt} ms"
                    st.session_state.do_status = "error"
                st.session_state.do_state = "result"
                st.rerun()

        with col2:
            if st.button("Ignore", use_container_width=True, key="do_pass"):
                rt = round((time.perf_counter() - st.session_state.do_start_time) * 1000)
                save_game_result(astronaut_id, GAME_NAME, rt, success=not is_go)

                if not is_go:
                    st.session_state.do_msg = f"Hazard avoided. Decision time: {rt} ms."
                    st.session_state.do_rt = f"{rt} ms"
                    st.session_state.do_status = "success"
                else:
                    st.session_state.do_msg = f"Missed valid supply capsule ({rt} ms)."
                    st.session_state.do_rt = f"{rt} ms"
                    st.session_state.do_status = "error"
                st.session_state.do_state = "result"
                st.rerun()

    elif st.session_state.do_state == "result":
        is_ok = st.session_state.do_status == "success"
        accent = "#10B981" if is_ok else "#F59E0B"
        badge = "NOMINAL RESPONSE" if is_ok else "SIMULATION ERROR"
        rt_text = escape(st.session_state.get("do_rt", "—"))
        msg_text = escape(st.session_state.do_msg)

        btn_col, info_col = st.columns([0.75, 1.25], gap="medium")
        with btn_col:
            if st.button("Reset Airlock", key="do_retry"):
                st.session_state.do_state = "idle"
                st.rerun()
        with info_col:
            st.markdown(
                f'<div class="nasa-sub-box nasa-game-desc" style="border-left-color: {accent};">'
                f'<div class="nasa-status-heading" style="color: {accent};">{badge}</div>'
                f'<div style="font-size: 24px; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">{rt_text}</div>'
                f'<p class="nasa-note">{msg_text}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_ranking():
    st.markdown(
        '<div class="nasa-card-header">'
        '<span class="nasa-card-title">Crew Leaderboard</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    render_leaderboard(GAME_NAME)