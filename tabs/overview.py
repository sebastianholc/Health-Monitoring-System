import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from html import escape

import streamlit as st

from astronaut import DEFAULT_DB
from health_assessment import Assessment, Finding, RULES, assess_health

SCHEDULE_DB = DEFAULT_DB.with_name("astronaut_health_demo_30d.db")


def next_test(astronaut_id, now):
    """Find the next scheduled test and format the time remaining in UTC."""
    uri = SCHEDULE_DB.resolve().as_uri() + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            row = connection.execute("""
                SELECT name, scheduled_at_utc
                FROM medical_tests
                WHERE astronaut_id = ? AND scheduled_at_utc > ?
                ORDER BY scheduled_at_utc, test_id
                LIMIT 1
            """, (astronaut_id, now.strftime("%Y-%m-%d %H:%M:%S"))).fetchone()
        if row is None:
            return "N/A", "No upcoming tests", ""

        name, scheduled_at = row
        scheduled = datetime.fromisoformat(scheduled_at).replace(tzinfo=timezone.utc)
    except (sqlite3.Error, ValueError):
        return "N/A", "Schedule unavailable", ""

    total_minutes = int((scheduled - now).total_seconds() // 60)
    days, remaining = divmod(total_minutes, 1440)
    hours, minutes = divmod(remaining, 60)
    countdown = f"{days:02d}d {hours:02d}h {minutes:02d}m" if total_minutes else "< 1 min"
    return countdown, name, scheduled.strftime("%Y-%m-%d %H:%M UTC")


@st.fragment(run_every="60s")
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
    justify-content: flex-start;
    max-height: 220px;
    min-height: 0;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #475569 #111625;
    padding-right: 4px;
}
.ai-focus-item {
    flex-shrink: 0;
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

    name_parts = astronaut.name.split(maxsplit=1)
    first_name = escape(name_parts[0]) if name_parts else "N/A"
    surname = escape(name_parts[1]) if len(name_parts) > 1 else "N/A"
    gender = escape(astronaut.gender or "N/A")
    age = astronaut.age()
    age_html = f'{age}<span class="param-unit">yrs</span>' if age is not None else "N/A"

    try:
        assessment = assess_health(astronaut.id, SCHEDULE_DB)
    except (sqlite3.Error, ValueError):
        assessment = Assessment(
            None,
            (Finding("Telemetry unavailable", "high", "Check the SQLite file and sample timestamps."),),
            0,
        )

    def measurement(code, unit, spec="g"):
        value = assessment.latest_values.get(code)
        if value is None:
            return "N/A"
        return f'{value:{spec}}<span class="param-unit">{unit}</span>'

    mass = measurement("body_mass_kg", "kg")
    height = measurement("height_cm", "cm")
    temperature = measurement("temperature_c", "°C", ".2f")
    heart_rate = measurement("heart_rate_bpm", "BPM")
    spo2 = measurement("spo2_pct", "%")
    sleep_score = measurement("sleep_score", "/ 100")
    sleep_progress = max(0, min(100, assessment.latest_values.get("sleep_score", 0)))
    sleep_hue = (
        0.9 * sleep_progress if sleep_progress <= 50
        else 45 + 2 * (sleep_progress - 50)
    )
    sleep_color = f"hsl({sleep_hue:.1f}, 80%, 46%)"

    status_text = "GO" if assessment.is_go else "NO GO"
    status_class = "status-badge-go" if assessment.is_go else "status-badge-nogo"
    card_alert_class = "" if assessment.is_go else "nasa-card-alert"
    status_detail = (
        ("Review the monitoring notes." if assessment.findings else "All configured demo checks passed.")
        if assessment.is_go else "Review the findings before proceeding in the demo."
    )
    mission_time = escape(assessment.mission_time or "Unavailable")

    focus_items_html = "".join(
        f'<div class="ai-focus-item priority-{item.priority}">'
        f'<div class="ai-focus-top">'
        f'<span class="ai-focus-title">{escape(item.title)}</span>'
        f'<span class="ai-badge-{item.priority}">'
        f'{"Review" if item.priority == "high" else "Monitor"}</span>'
        f'</div>'
        f'<p class="ai-focus-desc">{escape(item.description)}</p>'
        f'</div>'
        for item in assessment.findings
    ) or '<p class="sub-note">No findings under the configured demo rules.</p>'

    countdown, test_name, test_time = next_test(astronaut.id, datetime.now(timezone.utc))

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
<div class="param-value">{gender}</div>
</div>
<div class="param-item">
<div class="param-label">Age</div>
<div class="param-value">{age_html}</div>
</div>
<div class="param-item">
<div class="param-label">Weight</div>
<div class="param-value">{mass}</div>
</div>
<div class="param-item">
<div class="param-label">Height</div>
<div class="param-value">{height}</div>
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
<span class="param-value">{temperature}</span>
</div>
<div class="param-row">
<span class="param-label">Heart Rate</span>
<span class="param-value">{heart_rate}</span>
</div>
<div class="param-row">
<span class="param-label">Saturation</span>
<span class="param-value">{spo2}</span>
</div>
</div>
</div>
<div class="nasa-card">
<div class="nasa-card-header">
<span class="nasa-card-title">Focus Areas</span>
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
<span class="nasa-card-title">Space Walk // Demo GO - NO GO</span>
</div>
<div class="eva-status-box">
<div>
<div class="param-label">Readiness Status</div>
<div style="font-size: 12.5px; color: #CBD5E1; margin-top: 3px;">
{status_detail}
</div>
</div>
<div class="{status_class}">{status_text}</div>
</div>
<div class="eva-checks">
<span class="eva-pill">Checked: {assessment.checked_count}/{len(RULES)}</span>
<span class="eva-pill">Mission time: {mission_time}</span>
</div>
</div>
<div class="nasa-card">
<div class="nasa-card-header">
<span class="nasa-card-title">Last Sleep Score</span>
</div>
<div>
<div style="display: flex; justify-content: space-between; align-items: baseline;">
<div class="param-value" style="font-size: 25px;">
{sleep_score}
</div>

</div>
<div class="progress-track">
<div class="progress-fill" style="width: {sleep_progress}%; background-color: {sleep_color};"></div>
</div>
</div>
</div>
<div class="nasa-card">
<div class="nasa-card-header">
<span class="nasa-card-title">Time to Next Test</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center;">
<div class="param-value" style="font-size: 23px; color: #60A5FA;">
{escape(countdown)}
</div>
<div style="text-align: right;">
<p class="sub-note" style="color: #F8FAFC; font-weight: 600;">
{escape(test_name)}
</p>
<p class="sub-note" style="margin-top: 2px;">
{escape(test_time)}
</p>
</div>
</div>
</div>
</div>
</div>
"""
    st.markdown(dashboard_html, unsafe_allow_html=True)
