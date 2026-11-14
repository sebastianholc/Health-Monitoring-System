import streamlit as st
from streamlit_option_menu import option_menu

from astronaut import Astronaut

from astronaut_health_charts import render_health_charts

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Health Monitoring System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# ASTRONAUT DATA
# ==========================================


astronaut_1 = Astronaut("Sebastian Holc",68,98,36.7)
astronaut_2 = Astronaut("Igor Zabłocki",75,97,36.5)
astronaut_3 = Astronaut("Adam Guziałek",62,99,36.8)

# Dictionary: astronaut name -> Astronaut object
astronauts = {
    astronaut_1.name: astronaut_1,
    astronaut_2.name: astronaut_2,
    astronaut_3.name: astronaut_3
}

astronauts_names = list(astronauts.keys())


# ==========================================
# PAGES
# ==========================================

def overview(astronaut):
    overview_css = """
<style>
.nasa-card {
    background-color: #111625;
    border: 1px solid #1E293B;
    border-top: 3px solid #0032A0;
    border-radius: 8px;
    padding: 20px 22px;
    margin-bottom: 20px;
    width: 100%;
    box-sizing: border-box;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
}

.nasa-card-alert {
    border-top: 3px solid #E4002B;
}

.nasa-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1E293B;
}

.nasa-card-title {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: #94A3B8;
    margin: 0;
}

/* Układ Personal Info: zdjęcie po lewej + siatka danych po prawej */
.personal-layout {
    display: flex;
    gap: 18px;
    align-items: stretch;
}

.astronaut-avatar {
    flex: 0 0 135px;
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #60A5FA;
    min-height: 145px;
}

.personal-fields {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
}

.info-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
}

.param-item {
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.param-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748B;
    margin-bottom: 4px;
}

.param-value {
    font-size: 19px;
    font-weight: 700;
    color: #F8FAFC;
}

.param-unit {
    font-size: 13px;
    font-weight: 500;
    color: #94A3B8;
    margin-left: 3px;
}

/* AI Focus Areas */
.ai-focus-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.ai-focus-item {
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-left: 3px solid #0032A0;
    border-radius: 6px;
    padding: 12px 14px;
}

.ai-focus-item.priority-high {
    border-left: 3px solid #E4002B;
}

.ai-focus-item.priority-medium {
    border-left: 3px solid #F59E0B;
}

.ai-focus-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
}

.ai-focus-title {
    font-size: 14px;
    font-weight: 700;
    color: #F8FAFC;
}

.ai-badge-high {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #E4002B;
    background-color: rgba(228, 0, 43, 0.15);
    border: 1px solid #E4002B;
    padding: 2px 8px;
    border-radius: 4px;
}

.ai-badge-medium {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #FBBF24;
    background-color: rgba(245, 158, 11, 0.12);
    border: 1px solid #F59E0B;
    padding: 2px 8px;
    border-radius: 4px;
}

.ai-focus-desc {
    font-size: 12.5px;
    color: #94A3B8;
    line-height: 1.45;
    margin: 0;
}

/* Status GO / NO GO */
.eva-status-box {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 12px;
}

.status-badge-go {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #10B981;
    background-color: rgba(16, 185, 129, 0.12);
    border: 1px solid #10B981;
    padding: 5px 16px;
    border-radius: 6px;
}

.status-badge-nogo {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #E4002B;
    background-color: rgba(228, 0, 43, 0.15);
    border: 1px solid #E4002B;
    padding: 5px 16px;
    border-radius: 6px;
}

.eva-checks {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.eva-pill {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    color: #CBD5E1;
    background-color: #080B10;
    border: 1px solid #1E293B;
    padding: 5px 10px;
    border-radius: 4px;
}

/* Pasek postępu dla Sleep Score */
.progress-track {
    width: 100%;
    height: 8px;
    background-color: #080B10;
    border-radius: 4px;
    overflow: hidden;
    margin: 12px 0 8px 0;
    border: 1px solid #1E293B;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #0032A0 0%, #2563EB 100%);
    border-radius: 4px;
}

.sub-note {
    font-size: 12px;
    color: #94A3B8;
    margin: 0;
}
</style>
"""
    st.markdown(overview_css, unsafe_allow_html=True)

    # Rozbicie imienia i nazwiska + dane przykładowe (mock)
    name_parts = astronaut.name.split(" ", 1)
    first_name = name_parts[0]
    surname = name_parts[1] if len(name_parts) > 1 else "N/A"

    mock_gender = "Male"
    mock_age = astronaut.age()
    mock_weight = 78.4
    mock_height = 182
    mock_sleep_score = 64
    mock_next_test_countdown = "02d 14h 30m"
    mock_next_test_name = "ECG & VO2 Max Screening"

    # Przykładowe wyniki analizy modelu AI pod przyszły backend
    mock_ai_focus = [
        {
            "title": "Sleep Recovery & REM Deficit",
            "priority": "high",  # "high" -> czerwony akcent, "medium" -> bursztynowy
            "badge": "Action Required",
            "description": "Deep sleep phase dropped by 24% over the last 3 cycles. Extend rest window by 45 min and limit blue-light exposure before sleep."
        },
        {
            "title": "Wellbeing & Mood Index",
            "priority": "medium",
            "badge": "Monitor",
            "description": "Subjective mood and stress resilience score trending downward (-12%). Schedule routine behavioral check-in and lower non-critical workload."
        }
    ]

    # Przykładowy warunek pod przyszły backend (True = GO, False = NO GO)
    is_eva_go = True
    status_text = "GO" if is_eva_go else "NO GO"
    status_class = "status-badge-go" if is_eva_go else "status-badge-nogo"
    card_alert_class = "" if is_eva_go else "nasa-card-alert"

    col_left, col_right = st.columns([1.25, 1], gap="large")

    # ==========================================
    # LEWA KOLUMNA: Personal Info + Basic Params + AI Focus
    # ==========================================
    with col_left:
        # 1. PERSONAL INFO
        personal_info_html = f"""
<div class="nasa-card">
    <div class="nasa-card-header">
        <span class="nasa-card-title">Personal Info</span>
    </div>
    <div class="personal-layout">
        <div class="astronaut-avatar">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="8" r="4"></circle>
                <path d="M5 20a7 7 0 0 1 14 0"></path>
                <circle cx="12" cy="8" r="6.5" stroke-dasharray="2 2" opacity="0.6"></circle>
            </svg>
        </div>
        <div class="personal-fields">
            <div class="param-item">
                <div class="param-label">Name</div>
                <div class="param-value">{first_name}</div>
            </div>
            <div class="param-item">
                <div class="param-label">Surname</div>
                <div class="param-value">{surname}</div>
            </div>
            <div class="param-item">
                <div class="param-label">Gender</div>
                <div class="param-value">{mock_gender}</div>
            </div>
            <div class="param-item">
                <div class="param-label">Age</div>
                <div class="param-value">{mock_age}<span class="param-unit">yrs</span></div>
            </div>
            <div class="param-item">
                <div class="param-label">Weight</div>
                <div class="param-value">{mock_weight}<span class="param-unit">kg</span></div>
            </div>
            <div class="param-item">
                <div class="param-label">Height</div>
                <div class="param-value">{mock_height}<span class="param-unit">cm</span></div>
            </div>
        </div>
    </div>
</div>
"""
        st.markdown(personal_info_html, unsafe_allow_html=True)

        # 2. BASIC PARAMS
        basic_params_html = f"""
<div class="nasa-card">
    <div class="nasa-card-header">
        <span class="nasa-card-title">Basic Params</span>
    </div>
    <div class="info-grid-3">
        <div class="param-item">
            <div class="param-label">Temperature</div>
            <div class="param-value">{astronaut.temperature}<span class="param-unit">°C</span></div>
        </div>
        <div class="param-item">
            <div class="param-label">Heart Rate</div>
            <div class="param-value">{astronaut.heart_rate}<span class="param-unit">BPM</span></div>
        </div>
        <div class="param-item">
            <div class="param-label">Saturation</div>
            <div class="param-value">{astronaut.spo2}<span class="param-unit">%</span></div>
        </div>
    </div>
</div>
"""
        st.markdown(basic_params_html, unsafe_allow_html=True)

        # 3. AI FOCUS AREAS (Analiza parametrów przez model AI)
        focus_items_html = ""
        for item in mock_ai_focus:
            priority_cls = "priority-high" if item["priority"] == "high" else "priority-medium"
            badge_cls = "ai-badge-high" if item["priority"] == "high" else "ai-badge-medium"
            focus_items_html += f"""
<div class="ai-focus-item {priority_cls}">
    <div class="ai-focus-top">
        <span class="ai-focus-title">{item["title"]}</span>
        <span class="{badge_cls}">{item["badge"]}</span>
    </div>
    <p class="ai-focus-desc">{item["description"]}</p>
</div>
"""

        ai_focus_html = f"""
<div class="nasa-card">
    <div class="nasa-card-header">
        <span class="nasa-card-title">AI Focus Areas</span>
    </div>
    <div class="ai-focus-list">
        {focus_items_html}
    </div>
</div>
"""
        st.markdown(ai_focus_html, unsafe_allow_html=True)

    # ==========================================
    # PRAWA KOLUMNA: Space Walk + Sleep Score + Next Test
    # ==========================================
    with col_right:
        # 4. GO / NO GO FOR SPACE WALK
        eva_status_html = f"""
<div class="nasa-card {card_alert_class}">
    <div class="nasa-card-header">
        <span class="nasa-card-title">Space Walk // GO - NO GO</span>
    </div>
    <div class="eva-status-box">
        <div>
            <div class="param-label">Readiness Status</div>
            <div style="font-size: 13px; color: #CBD5E1; margin-top: 4px;">
                All primary biometric thresholds nominal
            </div>
        </div>
        <div class="{status_class}">{status_text}</div>
    </div>
    <div class="eva-checks">
        <span class="eva-pill">CARDIO: NOMINAL</span>
        <span class="eva-pill">O2 SAT: OPTIMAL</span>
        <span class="eva-pill">THERMAL: STABLE</span>
    </div>
</div>
"""
        st.markdown(eva_status_html, unsafe_allow_html=True)

        # 5. LAST SLEEP SCORE
        sleep_html = f"""
<div class="nasa-card">
    <div class="nasa-card-header">
        <span class="nasa-card-title">Last Sleep Score</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: baseline;">
        <div class="param-value" style="font-size: 28px;">
            {mock_sleep_score}<span class="param-unit" style="font-size: 15px;">/ 100</span>
        </div>
        <p class="sub-note">Duration: 6h 15m • REM 15% • Deep 12%</p>
    </div>
    <div class="progress-track">
        <div class="progress-fill" style="width: {mock_sleep_score}%;"></div>
    </div>
</div>
"""
        st.markdown(sleep_html, unsafe_allow_html=True)

        # 6. TIME TO NEXT TEST
        next_test_html = f"""
<div class="nasa-card">
    <div class="nasa-card-header">
        <span class="nasa-card-title">Time to Next Test</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div class="param-value" style="font-size: 26px; color: #60A5FA;">
            {mock_next_test_countdown}
        </div>
        <div style="text-align: right;">
            <p class="sub-note" style="color: #F8FAFC; font-weight: 600;">
                {mock_next_test_name}
            </p>
            <p class="sub-note" style="margin-top: 2px;">
                Med-Bay Module B • 08:00 UTC
            </p>
        </div>
    </div>
</div>
"""
        st.markdown(next_test_html, unsafe_allow_html=True)



def plots(astronaut):
    render_health_charts()


def measurments(astronaut):
    st.title("Recovery")
    st.write("Recovery monitoring")


def assistant(astronaut):
    st.title("Health Assistant")
    st.write("AI Health Assistant")

def gym(astronaut):
        st.title("Astro Gym")


pages = {
    "Overview": overview,
    "Plots": plots,
    "Measurments": measurments,
    "Assistant": assistant,
    "Gym": gym
}

pages_names = list(pages.keys())


# ==========================================
# SIDEBAR
# ==========================================

def sidebar():

    css = """
    <style>

        /* ==================================
           GLOBAL THEME & MAIN AREA (Mission Control)
        ================================== */

        /* Kosmiczna czerń / głęboki granat w tle */
        [data-testid="stAppViewContainer"] {
            background-color: #080B10 !important; 
        }

        [data-testid="stHeader"] {
            display: none !important;
        }

        [data-testid="stMain"] {
            background-color: #080B10 !important;
        }

        /* Zerujemy główny padding, aby górny pasek dotykał idealnie krawędzi */
        [data-testid="stMainBlockContainer"] {
            padding: 0 !important;
            max-width: 100% !important;
        }

        /* Nadajemy padding dla wszystkich elementów POZA górnym paskiem (Astronaut Selector to first-child) */
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div {
            padding-left: 3rem !important;
            padding-right: 3rem !important;
        }

        /* Upewniamy się, że pierwszy element (Astronaut Selector) ma padding = 0 */
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:first-child {
            padding-left: 0 !important;
            padding-right: 0 !important;
        }

        /* Dodajemy margines górny dla właściwej zawartości strony (żeby nie przyklejała się do paska) */
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(2) {
            padding-top: 2rem !important;
        }


        /* ==================================
           SIDEBAR
        ================================== */

        [data-testid="stSidebar"] {
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            background-color: #111625 !important;
            border-right: 1px solid #1E293B !important;
            cursor: default !important;
        }

        [data-testid="stSidebar"] > div {
            width: 280px !important;
            background-color: #111625 !important;
        }

        [data-testid="stSidebarHeader"] {
            display: none !important;
        }

        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"] {
            padding: 0 !important;
            background-color: #111625 !important;
        }

        [data-testid="stSidebar"] iframe {
            width: 100% !important;
            height: 100vh !important;
            min-height: 100vh !important;
            display: block !important;
            border: none !important;
        }

        /* Usunięcie resizera */
        [data-testid="stSidebarResizeHandle"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {
            display: none !important;
            width: 0 !important;
            pointer-events: none !important;
            visibility: hidden !important;
            cursor: default !important;
        }


        /* ==================================
           ASTRONAUT SELECTOR (Top Bar)
        ================================== */

        .st-key-astronaut_selector {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            background-color: #111625 !important; 
            border-bottom: none !important; /* Usunięto czerwoną linię */
            box-shadow: 0px 4px 15px rgba(0,0,0,0.6) !important;
        }

        .st-key-astronaut_selector > div {
            width: 100% !important;
            max-width: none !important;
        }

        [data-testid="stCustomComponentV1"] {
            width: 100% !important;
            max-width: none !important;
        }

        .st-key-astronaut_selector iframe {
            width: 100% !important;
            max-width: 100% !important;
            display: block !important;
            border: none !important;
        }

    </style>
    """

    with st.sidebar:

        st.markdown(css, unsafe_allow_html=True)

        selected = option_menu(
            menu_title="HEALTH MONITORING SYSTEM",
            options=pages_names,
            icons=[
                "grid",
                "heart-pulse",
                "activity",
                "moon",
                "brain"
            ],
            menu_icon=" ",
            default_index=0,
            orientation="vertical",
            key="sidebar_navigation",

            styles={
                "container": {
                    "padding": "0!important",
                    "background-color": "#111625",
                    "width": "100%",
                    "height": "100vh",
                    "border-radius": "0",
                },
                "menu-title": {
                    "font-size": "14px",
                    "font-weight": "800",
                    "color": "#94A3B8",
                    "padding": "25px 15px",
                    "letter-spacing": "2px",
                },
                "icon": {
                    "color": "#FFFFFF",
                    "font-size": "18px",
                },
                "nav": {
                    "display": "flex",
                    "flex-direction": "column",
                    "height": "calc(100vh - 70px)",
                },
                "nav-item": {
                    "width": "100%",
                },
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "4px 0", # Podświetlenie przylega do krawędzi (brak przerw)
                    "padding": "12px 20px", # Zrekompensowane paddingiem
                    "color": "#CBD5E1",
                    "border-radius": "8px",
                    "width": "100%", # Na pełną szerokość
                    "transition": "all 0.2s",
                },
                "nav-link-selected": {
                    "background-color": "#0032A0", # NASA Blue
                    "color": "#FFFFFF",
                    "font-weight": "600",
                },
            }
        )

    return selected




# ==========================================
# MAIN APPLICATION
# ==========================================

selected_page = sidebar()


# ==========================================
# ASTRONAUT SELECTION
# ==========================================

astronaut_name = option_menu(
    menu_title=None,

    options=astronauts_names,

    icons=[
        "person-badge",
        "person-badge",
        "person-badge"
    ],

    default_index=0,
    orientation="horizontal",
    key="astronaut_selector",

    styles={
        "container": {
            "padding": "0!important",
            "margin": "0",
            "background-color": "#111625",
            "width": "100%",
            "max-width": "none",
            "border-radius": "0",
        },
        "nav": {
            "display": "flex",
            "flex-direction": "row",
            "flex-wrap": "nowrap",
            "width": "100%",
        },
        "nav-item": {
            "flex": "1 1 0%",
            "min-width": "0",
        },
        "nav-link": {
            "font-size": "15px",
            "text-align": "center",
            "margin": "0",          # Usunięty wizualny "padding" (margines zewnętrzny)
            "padding": "15px 0",    # Wewnętrzny odstęp dla odpowiedniej wysokości paska
            "color": "#CBD5E1",
            "border-radius": "8px", # Zostawione same zaokrąglone rogi
            "width": "100%",        # Podświetlenie na pełną szerokość elementu
            "white-space": "nowrap",
            "transition": "background-color 0.2s",
        },
        "nav-link-selected": {
            "background-color": "#0032A0", # NASA Blue
            "color": "#FFFFFF",
            "font-weight": "600",
        },
        "icon": {
            "color": "#FFFFFF",
            "font-size": "18px",
        },
    }
)


# ==========================================
# DISPLAY SELECTED PAGE
# ==========================================

# Get selected astronaut object
astronaut_data = astronauts[astronaut_name]

# Display selected page
pages[selected_page](astronaut_data)