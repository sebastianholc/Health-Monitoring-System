import streamlit as st
from streamlit_option_menu import option_menu

from astronaut import Astronaut

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
    st.title("Health Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Heart Rate", f'{astronaut.heart_rate} BPM')
    col2.metric("SpO2", f'{astronaut.spo2}%')
    col3.metric("Temperature", f'{astronaut.temperature} °C')


def vitals(astronaut):
    st.title("Vital Signs")
    st.write("Detailed vital signs analysis")


def activity(astronaut):
    st.title("Activity")
    st.write("Activity monitoring")


def recovery(astronaut):
    st.title("Recovery")
    st.write("Recovery monitoring")


def assistant(astronaut):
    st.title("Health Assistant")
    st.write("AI Health Assistant")


pages = {
    "Overview": overview,
    "Vitals": vitals,
    "Activity": activity,
    "Recovery": recovery,
    "Assistant": assistant
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