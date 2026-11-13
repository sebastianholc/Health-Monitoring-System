import streamlit as st
from streamlit_option_menu import option_menu


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

astronauts = {
    "Astronaut 1": {
        "heart_rate": 68,
        "spo2": 98,
        "temperature": 36.7
    },
    "Astronaut 2": {
        "heart_rate": 75,
        "spo2": 97,
        "temperature": 36.5
    },
    "Astronaut 3": {
        "heart_rate": 62,
        "spo2": 99,
        "temperature": 36.8
    }
}


# ==========================================
# DASHBOARD PAGES
# ==========================================

def overview(data):
    st.title("Health Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Heart Rate", f'{data["heart_rate"]} BPM')
    col2.metric("SpO2", f'{data["spo2"]}%')
    col3.metric("Temperature", f'{data["temperature"]} °C')


def vitals(data):
    st.title("Vital Signs")
    st.write("Detailed vital signs analysis")


def activity(data):
    st.title("Activity")
    st.write("Activity monitoring")


def recovery(data):
    st.title("Recovery")
    st.write("Recovery monitoring")


def assistant(data):
    st.title("Health Assistant")
    st.write("AI Health Assistant")


# ==========================================
# SIDEBAR
# ==========================================

def sidebar():

    css = """
    <style>

        /* ==================================
           SIDEBAR
        ================================== */

        [data-testid="stSidebar"] {
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            background-color: #111827 !important;
        }

        [data-testid="stSidebar"] > div {
            width: 280px !important;
            background-color: #111827 !important;
        }

        /* Remove sidebar header and spacing */

        [data-testid="stSidebarHeader"] {
            display: none !important;
        }

        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"] {
            padding: 0 !important;
            background-color: #111827 !important;
        }

        /* Sidebar iframe */

        [data-testid="stSidebar"] iframe {
            width: 100% !important;
            height: 100vh !important;
            min-height: 100vh !important;
            display: block !important;
            border: none !important;
        }

        /* Hide sidebar controls */

        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarResizeHandle"] {
            display: none !important;
        }


        /* ==================================
           MAIN AREA
        ================================== */

        /* Hide Streamlit top header */

        [data-testid="stHeader"] {
            display: none !important;
        }

        /* Remove main area spacing */

        [data-testid="stMain"] {
            padding: 0 !important;
            margin: 0 !important;
        }

        [data-testid="stMainBlockContainer"] {
            width: 100% !important;
            max-width: none !important;
            padding: 0 !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }


        /* ==================================
           ASTRONAUT SELECTOR
        ================================== */

        /* Component wrapper */

        .st-key-astronaut_selector {
            width: 100% !important;
            max-width: none !important;
            min-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }

        /* Internal component wrapper */

        .st-key-astronaut_selector > div {
            width: 100% !important;
            max-width: none !important;
        }

        [data-testid="stCustomComponentV1"] {
            width: 100% !important;
            max-width: none !important;
        }

        /* Component iframe */

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
            options=[
                "Overview",
                "Vitals",
                "Activity",
                "Recovery",
                "Assistant"
            ],
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
                    "background-color": "#111827",
                    "width": "100%",
                    "height": "100vh",
                },
                "menu-title": {
                    "font-size": "16px",
                    "font-weight": "bold",
                    "color": "#FFFFFF",
                    "padding": "20px 15px",
                },
                "icon": {
                    "color": "#9CA3AF",
                    "font-size": "20px",
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
                    "margin": "5px 0px",
                    "padding": "12px 15px",
                    "color": "#D1D5DB",
                    "border-radius": "8px",
                    "width": "100%",
                },
                "nav-link-selected": {
                    "background-color": "#2563EB",
                    "color": "#FFFFFF",
                    "font-weight": "600",
                },
            }
        )

    return selected


# ==========================================
# PAGE SELECTION
# ==========================================

pages = {
    "Overview": overview,
    "Vitals": vitals,
    "Activity": activity,
    "Recovery": recovery,
    "Assistant": assistant
}


# ==========================================
# MAIN APPLICATION
# ==========================================

selected_page = sidebar()


# ==========================================
# ASTRONAUT SELECTION
# ==========================================

astronaut_name = option_menu(
    menu_title=None,

    options=list(astronauts.keys()),

    icons=[
        "person-circle",
        "person-circle",
        "person-circle"
    ],

    default_index=0,
    orientation="horizontal",
    key="astronaut_selector",

    styles={
        "container": {
            "padding": "0!important",
            "margin": "0",
            "background-color": "#111827",
            "width": "100%",
            "max-width": "none",
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
            "margin": "0",
            "padding": "12px 0",
            "color": "#D1D5DB",
            "border-radius": "0",
            "width": "100%",
            "white-space": "nowrap",
        },
        "nav-link-selected": {
            "background-color": "#2563EB",
            "color": "#FFFFFF",
            "font-weight": "600",
        },
        "icon": {
            "color": "#9CA3AF",
            "font-size": "20px",
        },
    }
)


# ==========================================
# DISPLAY SELECTED PAGE
# ==========================================

astronaut_data = astronauts[astronaut_name]

# showing selected page
pages[selected_page](astronaut_data)
