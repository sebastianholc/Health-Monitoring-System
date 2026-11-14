import math
import random
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = Path(__file__).resolve().parent / "astronaut_health_demo_30d.db"


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
            SELECT i.name AS "Astronauta",
                   MIN(CASE WHEN s.success = 1 THEN s.reaction_time_ms END)
                       AS "Najlepszy Czas (ms)",
                   COUNT(*) AS "Rozegrane Gry",
                   100.0 * AVG(s.success) AS "Celność (%)"
            FROM cognitive_game_scores AS s
            JOIN information AS i ON i.astronaut_id = s.astronaut_id
            WHERE s.game_name = ?
            GROUP BY s.astronaut_id, i.name
            ORDER BY "Najlepszy Czas (ms)" IS NULL, "Najlepszy Czas (ms)"
        """, connection, params=(game_name,))

    if not df.empty:
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Najlepszy Czas (ms)": st.column_config.NumberColumn(format="%d ms"),
                "Celność (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%")
            }
        )
    else:
        st.info("Brak danych dla tej symulacji. Zagraj jako pierwszy!")

# ==========================================
# GŁÓWNY MODUŁ GIER
# ==========================================
def cognitive_games_section(astronaut, *, ranking_panel=None):
    astronaut_id = getattr(astronaut, "id", None)
    if not astronaut_id:
        st.warning("Wybierz astronautę z identyfikatorem w bazie.")
        return

    try:
        init_games_db()
        game_choice = render_games(astronaut_id)
        if ranking_panel is None:
            render_ranking(game_choice)
        else:
            with ranking_panel:
                render_ranking(game_choice)
    except (sqlite3.Error, pd.errors.DatabaseError) as error:
        st.error(f"Nie udało się odczytać lub zapisać wyników gier: {error}")


def render_games(astronaut_id):
    if st.session_state.get("cognitive_game_owner") != astronaut_id:
        for key in list(st.session_state):
            if key.startswith(("di_", "do_", "at_", "cs_")):
                del st.session_state[key]
        st.session_state.cognitive_game_owner = astronaut_id

    st.subheader("Gry poznawcze")

    available_games = ("Docking Override", "Command Sequence")
    if st.session_state.get("active_game") not in available_games:
        st.session_state.active_game = available_games[0]

    game_choice = st.selectbox(
        "Wybierz test diagnostyczny:",
        available_games,
        index=available_games.index(st.session_state.active_game),
    )
    
    if game_choice != st.session_state.active_game:
        st.session_state.active_game = game_choice
        st.rerun()

    st.divider()

    # ==========================================
    # GRA 1: DEBRIS INTERCEPTOR
    # ==========================================
    if game_choice == "Debris Interceptor":
        st.markdown("### ☄️ Debris Interceptor")
        st.caption("Cel: Zneutralizuj kosmiczny śmieć tak szybko, jak to możliwe.")
        
        if "di_state" not in st.session_state:
            st.session_state.di_state = "idle"

        if st.session_state.di_state == "idle":
            if st.button("Rozpocznij Symulację", key="di_start"):
                st.session_state.di_state = "playing"
                st.session_state.di_target = random.randint(0, 8)
                st.session_state.di_start_time = time.perf_counter()
                st.rerun()

        elif st.session_state.di_state == "playing":
            cols = st.columns(3)
            for i in range(9):
                with cols[i % 3]:
                    if i == st.session_state.di_target:
                        if st.button("☄️ ZAAKCEPTUJ", key=f"di_btn_{i}", use_container_width=True):
                            rt = round((time.perf_counter() - st.session_state.di_start_time) * 1000)
                            st.session_state.di_rt = rt
                            
                            # ZAPIS DO BAZY DANYCH
                            save_game_result(astronaut_id, game_choice, rt, success=True)
                            
                            st.session_state.di_state = "result"
                            st.rerun()
                    else:
                        st.button("⬛", key=f"di_btn_{i}", use_container_width=True, disabled=True)

        elif st.session_state.di_state == "result":
            rt = st.session_state.di_rt
            if rt < 350:
                st.success(f"Błyskawiczna reakcja: **{rt} ms**. Gotowość bojowa: 100%.")
            else:
                st.warning(f"Czas reakcji: **{rt} ms**. Wykryto opóźnienie sensomotoryczne.")
            
            if st.button("Spróbuj ponownie", key="di_retry"):
                st.session_state.di_state = "idle"
                st.rerun()


    # ==========================================
    # GRA 2: DOCKING OVERRIDE
    # ==========================================
    elif game_choice == "Docking Override":
        st.markdown("### 📦 Docking Override")
        st.caption("Cel: Przechwytuj zaopatrzenie (📦), ignoruj zagrożenia (🪨/☀️). Badanie kontroli impulsów.")

        if "do_state" not in st.session_state:
            st.session_state.do_state = "idle"

        if st.session_state.do_state == "idle":
            if st.button("Inicjalizacja śluzy", key="do_start"):
                st.session_state.do_state = "waiting"
                st.rerun()

        elif st.session_state.do_state == "waiting":
            st.info("Oczekiwanie na zbliżenie obiektu...")
            time.sleep(random.uniform(1.0, 3.0))
            st.session_state.do_is_go = random.random() > 0.4
            st.session_state.do_start_time = time.perf_counter()
            st.session_state.do_state = "action"
            st.rerun()

        elif st.session_state.do_state == "action":
            is_go = st.session_state.do_is_go
            icon = "📦 Kapsuła Zaopatrzeniowa" if is_go else random.choice(["🪨 Mikrometeoryt", "☀️ Rozbłysk"])
            color = "green" if is_go else "red"
            
            st.markdown(f"<h2 style='text-align: center; color: {color};'>{icon}</h2>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            if col1.button("🟢 PRZECHWYĆ (CAPTURE)", use_container_width=True, key="do_cap"):
                rt = round((time.perf_counter() - st.session_state.do_start_time) * 1000)
                
                # ZAPIS DO BAZY DANYCH
                save_game_result(astronaut_id, game_choice, rt, success=is_go)
                
                if is_go:
                    st.session_state.do_msg = f"Sukces. Prawidłowo przechwycono w {rt} ms."
                    st.session_state.do_status = "success"
                else:
                    st.session_state.do_msg = f"Błąd krytyczny! Przechwycono zagrożenie (Fałszywie pozytywny). Czas: {rt} ms."
                    st.session_state.do_status = "error"
                st.session_state.do_state = "result"
                st.rerun()

            if col2.button("🔴 IGNORUJ (PASS)", use_container_width=True, key="do_pass"):
                rt = round((time.perf_counter() - st.session_state.do_start_time) * 1000)
                
                # W przypadku ignorowania ignorujemy tylko poprawnie. False negative zapisujemy jako zły wynik czasowy/błędny.
                save_game_result(astronaut_id, game_choice, rt, success=not is_go)
                
                if not is_go:
                    st.session_state.do_msg = f"Poprawnie zignorowano zagrożenie. Czas decyzji: {rt} ms."
                    st.session_state.do_status = "success"
                else:
                    st.session_state.do_msg = "Utracono zaopatrzenie! Kapsuła minęła stację (Pominięcie)."
                    st.session_state.do_status = "error"
                st.session_state.do_state = "result"
                st.rerun()

        elif st.session_state.do_state == "result":
            if st.session_state.do_status == "success":
                st.success(st.session_state.do_msg)
            else:
                st.error(st.session_state.do_msg)
            if st.button("Zresetuj śluzę", key="do_retry"):
                st.session_state.do_state = "idle"
                st.rerun()


    # ==========================================
    # GRA 3: ARTILLERY TRAJECTORY
    # ==========================================
    elif game_choice == "Artillery Trajectory":
        st.markdown("### 🎯 Artillery Trajectory Rapid-Fire")
        st.caption("Cel: Ustaw kąt strzału balistycznego w obliczu presji czasu, używając pamięci równań kinematyki.")

        if "at_state" not in st.session_state:
            st.session_state.at_state = "idle"

        if st.session_state.at_state == "idle":
            if st.button("Generuj koordynaty celu", key="at_start"):
                st.session_state.at_dist = random.randint(100, 250)
                st.session_state.at_v = 50
                st.session_state.at_start = time.perf_counter()
                st.session_state.at_state = "playing"
                st.rerun()

        elif st.session_state.at_state == "playing":
            d = st.session_state.at_dist
            v = st.session_state.at_v
            st.info(f"📍 Dystans: **{d} m** | 🚀 Prędkość: **{v} m/s** | 🌍 Grawitacja: **9.81 m/s²**")
            
            angle = st.slider("Wprowadź kąt elewacji [stopnie]:", min_value=0.0, max_value=45.0, step=0.1)
            
            if st.button("FIRE", type="primary"):
                rt_sec = time.perf_counter() - st.session_state.at_start
                rt_ms = round(rt_sec * 1000)
                
                val = (d * 9.81) / (v**2)
                val = min(1.0, max(-1.0, val)) 
                ideal_angle = math.degrees(math.asin(val)) / 2
                
                diff = abs(ideal_angle - angle)
                success = diff <= 2.0
                
                # ZAPIS DO BAZY DANYCH
                save_game_result(astronaut_id, game_choice, rt_ms, success)
                
                st.session_state.at_rt_sec = round(rt_sec, 2)
                st.session_state.at_diff = diff
                st.session_state.at_success = success
                st.session_state.at_state = "result"
                st.rerun()

        elif st.session_state.at_state == "result":
            diff = st.session_state.at_diff
            rt_sec = st.session_state.at_rt_sec
            
            if st.session_state.at_success:
                st.success(f"Trafienie bezpośrednie! Błąd kąta: {diff:.2f}°. Czas obliczeń: {rt_sec} s.")
            else:
                st.error(f"Pudło! Błąd rzędu {diff:.2f}°. Cel osiągnięto za późno lub trajektoria była błędna. Czas: {rt_sec} s.")
                
            if st.button("Kolejny cel", key="at_retry"):
                st.session_state.at_state = "idle"
                st.rerun()


    # ==========================================
    # GRA 4: COMMAND SEQUENCE
    # ==========================================
    elif game_choice == "Command Sequence":
        st.markdown("### 🧠 Command Sequence Match")
        st.caption("Cel: Zapamiętaj sekwencję systemów statku i odtwórz ją precyzyjnie z konsoli.")
        
        icons = ["🚀", "⚡", "📡", "🔋", "🛡️", "💧"]

        if "cs_state" not in st.session_state:
            st.session_state.cs_state = "idle"

        if st.session_state.cs_state == "idle":
            if st.button("Rozpocznij test pamięci", key="cs_start"):
                st.session_state.cs_target = random.sample(icons, 4)
                st.session_state.cs_user = []
                st.session_state.cs_state = "memorize"
                st.rerun()

        elif st.session_state.cs_state == "memorize":
            st.markdown("### ZAPAMIĘTAJ SEKWENCJĘ:")
            st.markdown(f"<h1 style='text-align: center; letter-spacing: 15px;'>{''.join(st.session_state.cs_target)}</h1>", unsafe_allow_html=True)
            
            if st.button("ZROZUMIANO - UKRYJ (Start pomiaru)"):
                st.session_state.cs_start_time = time.perf_counter()
                st.session_state.cs_state = "input"
                st.rerun()

        elif st.session_state.cs_state == "input":
            st.write(f"Wprowadzono: **{''.join(st.session_state.cs_user)}**")
            
            cols = st.columns(len(icons))
            for idx, icon in enumerate(icons):
                if cols[idx].button(icon, key=f"cs_btn_{idx}", use_container_width=True):
                    st.session_state.cs_user.append(icon)
                    if len(st.session_state.cs_user) == 4:
                        rt = round((time.perf_counter() - st.session_state.cs_start_time) * 1000)
                        target = st.session_state.cs_target
                        user = st.session_state.cs_user
                        success = (target == user)
                        
                        # ZAPIS DO BAZY DANYCH
                        save_game_result(astronaut_id, game_choice, rt, success)
                        
                        st.session_state.cs_rt = rt
                        st.session_state.cs_success = success
                        st.session_state.cs_state = "result"
                    st.rerun()
            
            if st.button("Wyczyść wpis"):
                st.session_state.cs_user = []
                st.rerun()

        elif st.session_state.cs_state == "result":
            target = st.session_state.cs_target
            user = st.session_state.cs_user
            rt = st.session_state.cs_rt
            
            if st.session_state.cs_success:
                st.success(f"Sekwencja prawidłowa! Przewodnictwo nerwowe w normie. Czas wprowadzania: {rt} ms.")
            else:
                st.error(f"Awaria systemu krytycznego. Oczekiwano: {''.join(target)}, Otrzymano: {''.join(user)}.")
                
            if st.button("Restart protokołu", key="cs_retry"):
                st.session_state.cs_state = "idle"
                st.rerun()

    return game_choice


def render_ranking(game_choice):
    st.subheader("Ranking załogi")
    st.caption(game_choice)
    render_leaderboard(game_choice)
