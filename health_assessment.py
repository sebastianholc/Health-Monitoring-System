"""Rule-based assessment of synthetic telemetry for the hackathon demo."""

import sqlite3
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import isfinite
from pathlib import Path

from astronaut import DEFAULT_DB


@dataclass(frozen=True)
class Rule:
    label: str
    unit: str
    minimum: float
    maximum: float
    max_age_minutes: int
    action: str
    priority: str = "high"


# Demo settings chosen for the synthetic data and its sampling intervals.
RULES = {
    "heart_rate_bpm": Rule("Heart rate", "bpm", 48, 105, 120, "Review the activity context."),
    "spo2_pct": Rule("SpO₂", "%", 94.5, 100, 120, "Verify the sensor reading."),
    "temperature_c": Rule("Temperature", "°C", 36, 37.6, 14 * 1440, "Review the latest recorded check."),
    "systolic_mmhg": Rule("Systolic pressure", "mmHg", 95, 140, 14 * 1440, "Review the paired pressure readings."),
    "diastolic_mmhg": Rule("Diastolic pressure", "mmHg", 60, 90, 14 * 1440, "Review the paired pressure readings."),
    "glucose_mg_dl": Rule("Blood glucose", "mg/dL", 75, 110, 31 * 1440, "Review the baseline lab entry."),
    "hrv_rmssd_ms": Rule("HRV", "ms", 30, 90, 1500, "Review the recorded recovery trend.", "medium"),
    "sleep_score": Rule("Sleep score", "/ 100", 75, 100, 1500, "Review the sleep log and recent scores.", "medium"),
    "fluid_intake_l": Rule("Fluid intake", "L/day", 2.2, 3.2, 1500, "Review the daily intake log.", "medium"),
}


@dataclass(frozen=True)
class Finding:
    title: str
    priority: str
    description: str


@dataclass(frozen=True)
class Assessment:
    mission_time: str | None
    findings: tuple[Finding, ...]
    checked_count: int
    latest_values: dict[str, float] = field(default_factory=dict)

    @property
    def is_go(self) -> bool:
        return self.checked_count == len(RULES) and all(item.priority == "medium" for item in self.findings)


def assess_health(astronaut_id: str | None, database_path: Path = DEFAULT_DB) -> Assessment:
    """Evaluate the latest sample per metric against the selected crew member's telemetry clock."""
    if astronaut_id is None:
        return Assessment(None, (Finding("Crew selection", "high", "Select a crew member with a database ID."),), 0)

    uri = Path(database_path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        rows = connection.execute("""
            SELECT m.metric_code, m.measured_at, m.value
            FROM measurements AS m
            WHERE m.astronaut_id = ?
              AND m.measured_at = (
                  SELECT MAX(latest.measured_at)
                  FROM measurements AS latest
                  WHERE latest.astronaut_id = m.astronaut_id
                    AND latest.metric_code = m.metric_code
              )
        """, (astronaut_id,)).fetchall()

    latest = {code: (timestamp, value) for code, timestamp, value in rows}
    if not latest:
        return Assessment(None, (Finding("Missing telemetry", "high", "Check the crew ID and available measurements."),), 0)

    mission_time = max(timestamp for timestamp, _ in latest.values())
    reference = datetime.fromisoformat(mission_time)
    findings = []
    checked = 0

    for code, rule in RULES.items():
        if code not in latest:
            findings.append(Finding(rule.label, "high", "No sample available. Check the data source."))
            continue

        timestamp, value = latest[code]
        age = reference - datetime.fromisoformat(timestamp)
        if age > timedelta(minutes=rule.max_age_minutes):
            findings.append(Finding(rule.label, "high", f"Last sample at {timestamp} is too old for this demo check. Refresh telemetry."))
            continue
        if not isinstance(value, (int, float)) or not isfinite(value):
            findings.append(Finding(rule.label, "high", "Invalid value. Verify the measurement."))
            continue

        checked += 1
        if not rule.minimum <= value <= rule.maximum:
            findings.append(Finding(
                rule.label,
                rule.priority,
                f"{value:g} {rule.unit} at {timestamp}. Demo range: "
                f"{rule.minimum:g}–{rule.maximum:g} {rule.unit}. {rule.action}",
            ))

    findings.sort(key=lambda item: item.priority != "high")
    latest_values = {
        code: value for code, (_, value) in latest.items()
        if isinstance(value, (int, float)) and isfinite(value)
    }
    return Assessment(mission_time, tuple(findings), checked, latest_values)
