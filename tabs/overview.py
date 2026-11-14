import streamlit as st

def overview(astronaut):
    overview_css = """
<style>
[data-testid="stMainBlockContainer"] {
    padding-bottom: 1rem !important;
}
.overview-grid {
    display: grid;
    grid-template-columns: 1.35fr 1fr;
    gap: 16px;
    align-items: stretch;
    width: 100%;
}
.left-col, .right-col {
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.left-bottom-row {
    display: grid;
    grid-template-columns: 0.82fr 1.18fr;
    gap: 16px;
    flex: 1;
}
.nasa-card {
    background-color: #111625;
    border: 1px solid #1E293B;
    border-top: 3px solid #0032A0;
    border-radius: 8px;
    padding: 15px 18px;
    margin: 0;
    width: 100%;
    box-sizing: border-box;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.nasa-card-alert {
    border-top: 3px solid #E4002B;
}
.nasa-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1E293B;
}
.nasa-card-title {
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: #94A3B8;
    margin: 0;
}
.personal-layout {
    display: flex;
    gap: 14px;
    align-items: stretch;
}
.astronaut-avatar {
    flex: 0 0 115px;
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #60A5FA;
}
.personal-fields {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}
.param-item {
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 9px 12px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.basic-params-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex: 1;
    justify-content: space-between;
}
.param-row {
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 11px 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.param-label {
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748B;
    margin-bottom: 2px;
}
.param-row .param-label {
    margin-bottom: 0;
}
.param-value {
    font-size: 17px;
    font-weight: 700;
    color: #F8FAFC;
}
.param-unit {
    font-size: 12px;
    font-weight: 500;
    color: #94A3B8;
    margin-left: 3px;
}
.ai-focus-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex: 1;
    justify-content: space-between;
}
.ai-focus-item {
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-left: 3px solid #0032A0;
    border-radius: 6px;
    padding: 10px 12px;
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
    gap: 8px;
    margin-bottom: 4px;
}
.ai-focus-title {
    font-size: 13px;
    font-weight: 700;
    color: #F8FAFC;
}
.ai-badge-high {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #E4002B;
    background-color: rgba(228, 0, 43, 0.15);
    border: 1px solid #E4002B;
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
}
.ai-badge-medium {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #FBBF24;
    background-color: rgba(245, 158, 11, 0.12);
    border: 1px solid #F59E0B;
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
}
.ai-focus-desc {
    font-size: 11.5px;
    color: #94A3B8;
    line-height: 1.38;
    margin: 0;
}
.eva-status-box {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: #080B10;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 11px 14px;
    margin-bottom: 10px;
}
.status-badge-go {
    font-size: 21px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #10B981;
    background-color: rgba(16, 185, 129, 0.12);
    border: 1px solid #10B981;
    padding: 4px 14px;
    border-radius: 6px;
}
.status-badge-nogo {
    font-size: 21px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #E4002B;
    background-color: rgba(228, 0, 43, 0.15);
    border: 1px solid #E4002B;
    padding: 4px 14px;
    border-radius: 6px;
}
.eva-checks {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.eva-pill {
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.7px;
    color: #CBD5E1;
    background-color: #080B10;
    border: 1px solid #1E293B;
    padding: 4px 9px;
    border-radius: 4px;
}
.progress-track {
    width: 100%;
    height: 7px;
    background-color: #080B10;
    border-radius: 4px;
    overflow: hidden;
    margin: 10px 0 2px 0;
    border: 1px solid #1E293B;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #0032A0 0%, #2563EB 100%);
    border-radius: 4px;
}
.sub-note {
    font-size: 11.5px;
    color: #94A3B8;
    margin: 0;
}
</style>
"""
    st.markdown(overview_css, unsafe_allow_html=True)

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

    mock_ai_focus = [
        {
            "title": "Sleep Recovery & REM Deficit",
            "priority": "high",
            "badge": "Action Required",
            "description": "Deep sleep dropped by 24% over the last 3 cycles. Extend rest window by 45 min before next shift."
        },
        {
            "title": "Wellbeing & Mood Index",
            "priority": "medium",
            "badge": "Monitor",
            "description": "Subjective mood score trending downward (-12%). Schedule behavioral check-in and reduce non-critical load."
        }
    ]

    is_eva_go = True
    status_text = "GO" if is_eva_go else "NO GO"
    status_class = "status-badge-go" if is_eva_go else "status-badge-nogo"
    card_alert_class = "" if is_eva_go else "nasa-card-alert"

    focus_items_html = "".join(
        f'<div class="ai-focus-item {"priority-high" if item["priority"] == "high" else "priority-medium"}">'
        f'<div class="ai-focus-top">'
        f'<span class="ai-focus-title">{item["title"]}</span>'
        f'<span class="{"ai-badge-high" if item["priority"] == "high" else "ai-badge-medium"}">{item["badge"]}</span>'
        f'</div>'
        f'<p class="ai-focus-desc">{item["description"]}</p>'
        f'</div>'
        for item in mock_ai_focus
    )

    dashboard_html = f"""
<div class="overview-grid">
<div class="left-col">
<div class="nasa-card">
<div class="nasa-card-header">
<span class="nasa-card-title">Personal Info</span>
</div>
<div class="personal-layout">
<div class="astronaut-avatar">
<svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
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
<div class="left-bottom-row">
<div class="nasa-card">
<div class="nasa-card-header">
<span class="nasa-card-title">Basic Params</span>
</div>
<div class="basic-params-list">
<div class="param-row">
<span class="param-label">Temperature</span>
<span class="param-value">{astronaut.temperature}<span class="param-unit">°C</span></span>
</div>
<div class="param-row">
<span class="param-label">Heart Rate</span>
<span class="param-value">{astronaut.heart_rate}<span class="param-unit">BPM</span></span>
</div>
<div class="param-row">
<span class="param-label">Saturation</span>
<span class="param-value">{astronaut.spo2}<span class="param-unit">%</span></span>
</div>
</div>
</div>
<div class="nasa-card">
<div class="nasa-card-header">
<span class="nasa-card-title">AI Focus Areas</span>
</div>
<div class="ai-focus-list">
{focus_items_html}
</div>
</div>
</div>
</div>
<div class="right-col">
<div class="nasa-card {card_alert_class}">
<div class="nasa-card-header">
<span class="nasa-card-title">Space Walk // GO - NO GO</span>
</div>
<div class="eva-status-box">
<div>
<div class="param-label">Readiness Status</div>
<div style="font-size: 12.5px; color: #CBD5E1; margin-top: 3px;">
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
<div class="nasa-card">
<div class="nasa-card-header">
<span class="nasa-card-title">Last Sleep Score</span>
</div>
<div>
<div style="display: flex; justify-content: space-between; align-items: baseline;">
<div class="param-value" style="font-size: 25px;">
{mock_sleep_score}<span class="param-unit" style="font-size: 14px;">/ 100</span>
</div>
<p class="sub-note">Duration: 6h 15m • REM 15% • Deep 12%</p>
</div>
<div class="progress-track">
<div class="progress-fill" style="width: {mock_sleep_score}%;"></div>
</div>
</div>
</div>
<div class="nasa-card">
<div class="nasa-card-header">
<span class="nasa-card-title">Time to Next Test</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center;">
<div class="param-value" style="font-size: 23px; color: #60A5FA;">
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
</div>
</div>
"""
    st.markdown(dashboard_html, unsafe_allow_html=True)
