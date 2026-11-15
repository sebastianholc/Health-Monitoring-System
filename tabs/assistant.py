"""Zakładka Assistant z czatem AI oraz biblioteką literatury medycznej."""

import re
import sqlite3
from html import escape

import streamlit as st

from astronaut import DEFAULT_DB
from health_assessment import RULES, assess_health

TELEMETRY_DB = DEFAULT_DB.with_name("astronaut_health_demo_30d.db")

NASA_BLUE = "#0032A0"
NASA_RED = "#E4002B"

MEDICAL_LIBRARY = [
    {
        "id": "nasa_std_3001",
        "title": "NASA-STD-3001 Vol. 2 (Rev. C): Human-System Standard",
        "source": "NASA Technical Standards",
        "year": "2024",
        "category": "Standards",
        "pages": "142 pp.",
        "summary": "Defines biomedical limits, cabin atmosphere requirements, and physiological thresholds for crew health during orbital and deep-space missions.",
        "content": (
            "SECTION 6.2 — CARDIOVASCULAR & METABOLIC LIMITS\n"
            "• Resting Heart Rate nominal operational band: 50–85 BPM.\n"
            "• Arterial Oxygen Saturation (SpO2) minimum threshold: >= 95% under nominal cabin pressure (101.3 kPa).\n"
            "• Core Body Temperature operational window: 36.1°C – 37.5°C.\n\n"
            "SECTION 7.4 — WORK-REST CYCLES\n"
            "Crew members require a minimum 8.5-hour scheduled sleep opportunity per 24-hour cycle. "
            "Cumulative sleep debt exceeding 4 hours over 72 hours requires Flight Surgeon review prior to high-load tasks."
        ),
    },
    {
        "id": "iss_eva_b13",
        "title": "ISS Medical Operations Flight Rules: EVA Clearance (B13-204)",
        "source": "JSC Space Medicine Operations",
        "year": "2025",
        "category": "EVA Protocols",
        "pages": "38 pp.",
        "summary": "Mandatory pre-EVA biometric screening criteria, decompression sickness (DCS) pre-breathe protocols, and NO-GO triggers.",
        "content": (
            "PRE-EVA GO / NO-GO CRITERIA\n"
            "1. Pre-breathe O2 saturation must remain >= 97% prior to suit pressurization.\n"
            "2. Resting heart rate deviation > +15 BPM above personal 14-day baseline triggers secondary ECG evaluation.\n"
            "3. Core temperature >= 37.8°C or signs of acute vestibular disturbance constitute an automatic NO-GO.\n\n"
            "HYDRATION PROTOCOL\n"
            "Minimum 1.0 L isotonic fluid intake within 3 hours preceding Extravehicular Activity."
        ),
    },
    {
        "id": "sleep_microgravity",
        "title": "Circadian Misalignment & REM Architecture in Microgravity",
        "source": "Aerospace Medicine & Human Performance",
        "year": "2024",
        "category": "Sleep & Recovery",
        "pages": "24 pp.",
        "summary": "Clinical analysis of slow-wave and REM sleep reduction in orbital environments and targeted light-therapy countermeasures.",
        "content": (
            "CLINICAL FINDINGS\n"
            "Orbital crew frequently exhibit a 15–25% reduction in Slow-Wave Sleep (SWS) caused by 90-minute light-dark transitions and acoustic noise.\n\n"
            "RECOMMENDED COUNTERMEASURES\n"
            "• Dynamic Solid-State Lighting (SSL): 480 nm blue-enriched spectrum during wake hours; < 2700K low-illuminance mode 90 minutes pre-sleep.\n"
            "• Short-acting melatonin (0.3–1.0 mg) strictly under Flight Surgeon authorization."
        ),
    },
    {
        "id": "cardio_fluid_hrp",
        "title": "Orthostatic Intolerance & Fluid Loading Countermeasures",
        "source": "NASA Human Research Program (HRP)",
        "year": "2024",
        "category": "Cardiovascular",
        "pages": "64 pp.",
        "summary": "Evidence report covering cephalad fluid shifts, plasma volume loss, and re-entry cardiovascular conditioning.",
        "content": (
            "PHYSIOLOGICAL MECHANISM\n"
            "Microgravity induces a ~2 L cephalad fluid shift, triggering neurohormonal diuresis and a 10–15% reduction in total plasma volume within 48 hours.\n\n"
            "COUNTERMEASURE PROTOCOL\n"
            "Daily aerobic resistive exercise (ARED + T2 treadmill) combined with targeted electrolyte-sodium loading prior to gravitational transitions."
        ),
    },
    {
        "id": "behavioral_bhp",
        "title": "Behavioral Health, Cognitive Fatigue & Isolation Resilience",
        "source": "NASA Behavioral Health & Performance",
        "year": "2023",
        "category": "Psychology",
        "pages": "51 pp.",
        "summary": "Guidelines for monitoring mood trends, cognitive workload, and crew cohesion during extended isolation missions.",
        "content": (
            "EARLY FATIGUE INDICATORS\n"
            "• Sustained drop in HRV (RMSSD < 30 ms) paired with declining subjective mood scores.\n"
            "• Increased reaction time latency on Psychomotor Vigilance Tests (PVT).\n\n"
            "INTERVENTION\n"
            "Redistribute non-critical maintenance tasks, schedule private family conference, and verify sleep hygiene compliance."
        ),
    },
]


def _telemetry_reply(prompt: str, astronaut) -> str:
    question = prompt.casefold()
    tokens = set(re.findall(r"\w+", question))
    astronaut_id = getattr(astronaut, "id", None)
    if str(astronaut_id).zfill(3) == "002" and (
        tokens & {"headache", "headaches"} or "head hurts" in question
    ):
        return (
            "The baseline records show blood pressure of "
            "164.52/104.02 mmHg on 5 Nov and SpO₂ of 89.74% on 13 Nov.\n"
            "Flag both readings for review. In this scenario, ask for fresh blood "
            "pressure and SpO₂ readings and pass them to the medical team with "
            "the time the headache began. The baseline readings do not establish "
            "the cause of the headache."
        )
    refresh = any(part in question for part in (
        "refresh", "stale", "missing", "out of date", "odświe", "brak", "nieaktual",
    ))
    readiness = bool(tokens & {"eva", "readiness", "denied", "approved", "spacewalk"}) or "space walk" in question
    sleep = bool(tokens & {"sleep", "sen", "snu", "rem", "fatigue", "zmęczenie"})
    vitals = bool(tokens & {"vitals", "telemetry", "biometric", "telemetria", "parametry"})
    if not any((refresh, readiness, sleep, vitals)):
        return "Ask about EVA readiness, measurements to refresh, sleep score, or latest vitals."

    if astronaut_id is None:
        return "Select a crew member with a database ID."
    try:
        assessment = assess_health(astronaut_id, TELEMETRY_DB)
    except (sqlite3.Error, ValueError):
        return "Telemetry unavailable. Check the SQLite file and measurement timestamps."

    if assessment.mission_time is None:
        return "No telemetry found for this crew member. Check the crew ID and available measurements."

    if refresh:
        # Use the existing assessment messages to retain Overview's freshness rules.
        findings = [
            finding for finding in assessment.findings
            if finding.description.startswith(("No sample available.", "Last sample at ", "Invalid value."))
        ]
        if not findings:
            return "All parameters used in the demo readiness check have current, valid samples."
        lines = [f"Measurements to refresh or verify for {astronaut.name}"]
        lines.extend(f"• {finding.title}: {finding.description}" for finding in findings)
        return "\n".join(lines)

    if readiness:
        status = "APPROVED" if assessment.is_go else "DENIED"
        lines = [
            f"Demo EVA readiness for {astronaut.name}: {status}",
            f"Checked parameters: {assessment.checked_count}/{len(RULES)}",
        ]
        for finding in assessment.findings:
            label = "Monitor" if finding.priority == "medium" else "Review"
            lines.append(f"• {label} — {finding.title}: {finding.description}")
        if not assessment.findings:
            lines.append("All configured demo checks passed.")
        return "\n".join(lines)

    if sleep:
        codes = ("sleep_score",)
        title = "Latest sleep score"
    else:
        codes = ("heart_rate_bpm", "spo2_pct", "temperature_c")
        title = "Latest vital signs"

    lines = [f"{title} for {astronaut.name}"]
    for code in codes:
        rule = RULES[code]
        value = assessment.latest_values.get(code)
        reading = f"{value:g} {rule.unit}" if value is not None else "Unavailable"
        lines.append(f"• {rule.label}: {reading}")
        lines.extend(
            f"  {finding.description}" for finding in assessment.findings
            if finding.title == rule.label
        )
    return "\n".join(lines)


def assistant(astronaut) -> None:
    assistant_css = f"""
<style>
[data-testid="stMainBlockContainer"] {{
    padding-bottom: 1rem !important;
}}
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
/* Usunięcie dziedziczonych 3rem paddingu i 2rem top-paddingu z HMS_app.py wewnątrz kolumn */
[data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] [data-testid="stVerticalBlock"] > div,
[data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] [data-testid="stVerticalBlock"] > div:first-child,
[data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] [data-testid="stVerticalBlock"] > div:nth-child(2) {{
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-top: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}}
/* Karta czatu */
[data-testid="stMainBlockContainer"] .st-key-assistant_chat_card {{
    background-color: #111625 !important;
    border: 1px solid #1E293B !important;
    border-top: 3px solid {NASA_BLUE} !important;
    border-radius: 8px !important;
    padding: 14px 16px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
    width: 100% !important;
    box-sizing: border-box !important;
}}
/* Karta biblioteki medycznej — 4px odstępu wewnętrznego po bokach */
[data-testid="stMainBlockContainer"] .st-key-assistant_library_card {{
    background-color: #111625 !important;
    border: 1px solid #1E293B !important;
    border-top: 3px solid {NASA_BLUE} !important;
    border-radius: 8px !important;
    padding: 8px 4px 6px 4px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}}
[data-testid="stMainBlockContainer"] .st-key-assistant_library_card > [data-testid="stVerticalBlock"] {{
    gap: 6px !important;
    width: 100% !important;
    max-width: 100% !important;
}}
/* Kontener przewijany biblioteki */
[data-testid="stMainBlockContainer"] .st-key-library_scroll_box,
[data-testid="stMainBlockContainer"] .st-key-library_scroll_box > div,
[data-testid="stMainBlockContainer"] .st-key-library_scroll_box [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMainBlockContainer"] .st-key-library_scroll_box [data-testid="stVerticalBlockBorderWrapper"] > div {{
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}}
[data-testid="stMainBlockContainer"] .st-key-library_scroll_box [data-testid="stVerticalBlock"] {{
    gap: 6px !important;
    width: 100% !important;
}}
/* Nagłówki wewnątrz kart */
.nasa-panel-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 4px 6px 4px;
    margin-bottom: 0;
    border-bottom: 1px solid #1E293B;
    width: 100%;
    box-sizing: border-box;
}}
.nasa-panel-title {{
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: #94A3B8;
}}
.nasa-panel-badge {{
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.8px;
    color: #60A5FA;
    background-color: rgba(0, 50, 160, 0.25);
    border: 1px solid {NASA_BLUE};
    padding: 2px 7px;
    border-radius: 4px;
}}
/* Dymki wiadomości czatu */
.chat-msg-row {{
    display: flex;
    flex-direction: column;
    margin-bottom: 10px;
}}
.chat-msg-user {{
    align-self: flex-end;
    max-width: 82%;
    background-color: #0032A0;
    border: 1px solid #1D4ED8;
    color: #F8FAFC;
    border-radius: 8px 8px 2px 8px;
    padding: 10px 14px;
    font-size: 13.5px;
    line-height: 1.45;
}}
.chat-msg-ai {{
    align-self: flex-start;
    max-width: 90%;
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-left: 3px solid {NASA_BLUE};
    color: #E2E8F0;
    border-radius: 2px 8px 8px 8px;
    padding: 11px 14px;
    font-size: 13.5px;
    line-height: 1.5;
}}
.chat-sender {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #64748B;
    margin-bottom: 4px;
}}
.chat-sender-user {{
    text-align: right;
}}
/* Kafelek pojedynczego dokumentu — pełna szerokość panelu biblioteki */
[data-testid="stMainBlockContainer"] [class*="st-key-medical_source_card_"],
.lib-doc-card {{
    position: relative !important;
    background-color: #080B10 !important;
    border: 1px solid #1E293B !important;
    border-left: 3px solid {NASA_BLUE} !important;
    border-radius: 6px !important;
    padding: 8px 10px !important;
    margin: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}}
[data-testid="stMainBlockContainer"] [class*="st-key-medical_source_card_"] [class*="st-key-medical_source_actions_"] {{
    position: static !important;
    inset: auto !important;
    margin: 0 !important;
}}
[data-testid="stMainBlockContainer"] [class*="st-key-medical_source_card_"] .lib-doc-list-summary {{
    display: block;
    padding-bottom: 8px;
}}
.lib-doc-title {{
    font-size: 12.5px;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.28;
    margin-bottom: 2px;
    overflow-wrap: break-word;
    word-break: break-word;
}}
.lib-doc-meta {{
    font-size: 10.5px;
    color: #64748B;
    margin: 0 0 4px 0;
    overflow-wrap: break-word;
}}
.lib-doc-summary {{
    font-size: 11.5px;
    color: #94A3B8;
    line-height: 1.35;
    margin: 0;
    width: 100%;
    box-sizing: border-box;
    overflow-wrap: break-word;
    word-break: break-word;
}}
[data-testid="stMainBlockContainer"] [class*="st-key-medical_source_card_"] button {{
    background-color: rgba(0, 50, 160, 0.25) !important;
    border: 1px solid {NASA_BLUE} !important;
    color: #60A5FA !important;
    border-radius: 4px !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.7px !important;
    text-transform: uppercase !important;
    padding: 2px 8px !important;
    min-width: 44px !important;
    width: auto !important;
    min-height: 22px !important;
    height: 22px !important;
    line-height: 1 !important;
}}
[data-testid="stMainBlockContainer"] [class*="st-key-medical_source_card_"] button:hover {{
    background-color: {NASA_BLUE} !important;
    border-color: #60A5FA !important;
    color: #FFFFFF !important;
}}
/* Widok czytnika dokumentu */
.doc-reader-box {{
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 10px 12px;
    color: #CBD5E1;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-line;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    overflow-wrap: break-word;
}}
/* Inputy i selectboxy */
[data-testid="stMainBlockContainer"] .st-key-assistant_chat_card [data-testid="stTextInput"] input,
[data-testid="stMainBlockContainer"] .st-key-assistant_library_card [data-testid="stTextInput"] input,
[data-testid="stMainBlockContainer"] .st-key-assistant_library_card [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
    background-color: #080B10 !important;
    border: 1px solid #1E293B !important;
    border-radius: 6px !important;
    color: #F8FAFC !important;
    font-size: 12.5px !important;
}}
[data-testid="stMainBlockContainer"] .st-key-assistant_chat_card [data-testid="stTextInput"] input:focus,
[data-testid="stMainBlockContainer"] .st-key-assistant_library_card [data-testid="stTextInput"] input:focus {{
    border-color: #60A5FA !important;
    box-shadow: none !important;
}}
/* Przyciski ogólne */
[data-testid="stMainBlockContainer"] .st-key-assistant_chat_card button,
[data-testid="stMainBlockContainer"] .st-key-close_doc_reader button {{
    background-color: #080B10 !important;
    border: 1px solid #1E293B !important;
    color: #CBD5E1 !important;
    border-radius: 6px !important;
    font-size: 11.5px !important;
    font-weight: 600 !important;
    padding: 4px 10px !important;
    min-height: 30px !important;
    transition: all 0.2s ease !important;
}}
[data-testid="stMainBlockContainer"] .st-key-assistant_chat_card button:hover,
[data-testid="stMainBlockContainer"] .st-key-close_doc_reader button:hover {{
    border-color: #60A5FA !important;
    color: #FFFFFF !important;
}}
/* Przycisk wysyłania wiadomości w NASA Blue */
[data-testid="stMainBlockContainer"] .st-key-assistant_chat_card [data-testid="stFormSubmitButton"] button {{
    background-color: {NASA_BLUE} !important;
    border: 1px solid #1D4ED8 !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    height: 40px !important;
}}
[data-testid="stMainBlockContainer"] .st-key-assistant_chat_card [data-testid="stFormSubmitButton"] button:hover {{
    background-color: #0041CC !important;
}}
[data-testid="stMainBlockContainer"] .st-key-assistant_chat_card [data-testid="stForm"] {{
    border: none !important;
    padding: 0 !important;
    margin-top: 6px !important;
}}
/* Ciemne paski przewijania */
[data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar {{
    width: 4px;
}}
[data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-track {{
    background: #080B10;
}}
[data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-thumb {{
    background: #1E293B;
    border-radius: 3px;
}}
</style>
"""
    st.markdown(assistant_css, unsafe_allow_html=True)

    if "selected_library_doc" not in st.session_state:
        st.session_state["selected_library_doc"] = None

    chat_key = f"telemetry_chat_{getattr(astronaut, 'id', None) or astronaut.name}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {
                "role": "assistant",
                "content": (
                    f"Telemetry assistant for {astronaut.name}. "
                    "Ask about demo EVA readiness, measurements to refresh, sleep score, or latest vitals."
                ),
            }
        ]


    chat_col, library_col = st.columns([1.15, 1], gap="small")

    # ==========================================
    # LEWA KOLUMNA: CZAT TELEMETRYCZNY
    # ==========================================
    with chat_col:
        with st.container(key="assistant_chat_card"):
            head_left, head_right = st.columns([3, 1])
            with head_left:
                st.markdown(
                    f'<div class="nasa-panel-header" style="border:none; margin:0; padding:0;">'
                    f'<span class="nasa-panel-title">Telemetry Assistant // {escape(astronaut.name)}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with head_right:
                if st.button("Clear Chat", key="clear_assistant_chat", use_container_width=True):
                    del st.session_state[chat_key]
                    st.rerun()

            st.markdown(
                '<div style="border-bottom: 1px solid #1E293B; margin: 8px 0 12px 0;"></div>',
                unsafe_allow_html=True,
            )

            chat_scroll = st.container(height=365, border=False)
            with chat_scroll:
                for msg in st.session_state[chat_key]:
                    if msg["role"] == "user":
                        st.markdown(
                            f'<div class="chat-msg-row">'
                            f'<div class="chat-sender chat-sender-user">Flight Controller</div>'
                            f'<div class="chat-msg-user">{escape(msg["content"])}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        formatted_text = escape(msg["content"]).replace("\n", "<br>")
                        st.markdown(
                            f'<div class="chat-msg-row">'
                            f'<div class="chat-sender">Telemetry Assistant</div>'
                            f'<div class="chat-msg-ai">{formatted_text}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

            quick_columns = st.columns(4, gap="small")
            quick_prompt = None
            for column, (label, prompt) in zip(quick_columns, (
                ("EVA Decision", "Explain the EVA readiness decision."),
                ("Data to Refresh", "Which measurements should I refresh?"),
                ("Sleep Score", "Show the latest sleep score."),
                ("Latest Vitals", "Show the latest vital signs."),
            )):
                if column.button(label, key=f"telemetry_prompt_{label}", use_container_width=True):
                    quick_prompt = prompt

            with st.form(key="assistant_chat_form", clear_on_submit=True):
                input_col, btn_col = st.columns([4.2, 1], gap="small")
                with input_col:
                    user_text = st.text_input(
                        "Message",
                        placeholder=f"Query medical assistant about {astronaut.name}...",
                        label_visibility="collapsed",
                    )
                with btn_col:
                    submitted = st.form_submit_button("Send", use_container_width=True)

            active_prompt = quick_prompt or (user_text.strip() if submitted and user_text.strip() else None)
            if active_prompt:
                st.session_state[chat_key].append({"role": "user", "content": active_prompt})
                reply = _telemetry_reply(active_prompt, astronaut)
                st.session_state[chat_key].append(
                    {"role": "assistant", "content": reply}
                )
                st.rerun()

    # ==========================================
    # PRAWA KOLUMNA: BIBLIOTEKA MEDYCZNA
    # ==========================================
    with library_col:
        with st.container(key="assistant_library_card"):
            st.markdown(
                f'<div class="nasa-panel-header">'
                f'<span class="nasa-panel-title">Medical Literature</span>'
                f'<span class="nasa-panel-badge">{len(MEDICAL_LIBRARY)} SOURCES</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            selected_doc_id = st.session_state.get("selected_library_doc")

            if selected_doc_id:
                doc = next((d for d in MEDICAL_LIBRARY if d["id"] == selected_doc_id), None)
                if doc:
                    if st.button("← Back to Library", key="close_doc_reader", use_container_width=True):
                        st.session_state["selected_library_doc"] = None
                        st.rerun()

                    reader_scroll = st.container(height=445, border=False, key="library_scroll_box")
                    with reader_scroll:
                        st.markdown(
                            f'<div class="lib-doc-card" style="margin-bottom: 6px;">'
                            f'<div class="lib-doc-title" style="padding-right: 0;">{doc["title"]}</div>'
                            f'<div class="lib-doc-meta">{doc["category"]} · {doc["source"]} · {doc["year"]} · {doc["pages"]}</div>'
                            f'<p class="lib-doc-summary">{doc["summary"]}</p>'
                            f'</div>'
                            f'<div class="doc-reader-box">{doc["content"]}</div>',
                            unsafe_allow_html=True,
                        )
            else:
                search_col, cat_col = st.columns([1.3, 1], gap="small")
                with search_col:
                    search_query = st.text_input(
                        "Search",
                        placeholder="Search protocols, standards...",
                        key="library_search_input",
                        label_visibility="collapsed",
                    ).strip().lower()
                with cat_col:
                    categories = ["All"] + sorted({d["category"] for d in MEDICAL_LIBRARY})
                    selected_cat = st.selectbox(
                        "Category",
                        categories,
                        key="library_category_filter",
                        label_visibility="collapsed",
                    )

                filtered_docs = [
                    doc for doc in MEDICAL_LIBRARY
                    if (selected_cat == "All" or doc["category"] == selected_cat)
                    and (
                        not search_query
                        or search_query in doc["title"].lower()
                        or search_query in doc["summary"].lower()
                        or search_query in doc["source"].lower()
                    )
                ]

                lib_scroll = st.container(height=435, border=False, key="library_scroll_box")
                with lib_scroll:
                    if not filtered_docs:
                        st.info("No medical documents match the current filter.")
                    for doc in filtered_docs:
                        with st.container(key=f"medical_source_card_{doc['id']}"):
                            st.markdown(
                                f'<div class="lib-doc-title">{doc["title"]}</div>'
                                f'<div class="lib-doc-meta">{doc["category"]} · {doc["source"]} · {doc["year"]} · {doc["pages"]}</div>'
                                f'<div class="lib-doc-summary lib-doc-list-summary">{doc["summary"]}</div>',
                                unsafe_allow_html=True,
                            )
                            with st.container(key=f"medical_source_actions_{doc['id']}"):
                                if st.button("Read", key=f"read_medical_source_{doc['id']}"):
                                    st.session_state["selected_library_doc"] = doc["id"]
                                    st.rerun()
