"""Astronaut profiles and latest measurements from the local SQLite database."""

import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path


DEFAULT_DB = Path(__file__).with_name("astronaut_health_demo.db")


class Astronaut:
    def __init__(
        self,
        name,
        heart_rate,
        spo2,
        temperature,
        *,
        astronaut_id=None,
        gender=None,
        date_of_birth=None,
        age_years=None,
    ):
        self.id = astronaut_id
        self.name = name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.age_years = age_years
        self.heart_rate = heart_rate
        self.spo2 = spo2
        self.temperature = temperature

    def age(self, current_time=None):
        if current_time is None and self.age_years is not None:
            return self.age_years
        if self.date_of_birth is None:
            return None

        birth_date = date.fromisoformat(self.date_of_birth)
        if current_time is None:
            reference = date.today()
        elif "/" in current_time:
            reference = datetime.strptime(current_time, "%d/%m/%Y").date()
        else:
            reference = date.fromisoformat(current_time)

        birthday_passed = (reference.month, reference.day) >= (
            birth_date.month,
            birth_date.day,
        )
        return reference.year - birth_date.year - (not birthday_passed)


def load_astronauts(database_path=DEFAULT_DB):
    """Return profiles, each with the latest reading for each overview metric."""
    uri = Path(database_path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        rows = connection.execute("""
            SELECT a.astronaut_id, a.name, a.gender, a.date_of_birth, a.age,
                   (SELECT value FROM measurements
                    WHERE astronaut_id = a.astronaut_id AND metric_code = 'heart_rate_bpm'
                    ORDER BY measured_at DESC LIMIT 1),
                   (SELECT value FROM measurements
                    WHERE astronaut_id = a.astronaut_id AND metric_code = 'spo2_pct'
                    ORDER BY measured_at DESC LIMIT 1),
                   (SELECT value FROM measurements
                    WHERE astronaut_id = a.astronaut_id AND metric_code = 'temperature_c'
                    ORDER BY measured_at DESC LIMIT 1)
            FROM information AS a
            ORDER BY a.astronaut_id
        """).fetchall()

    return [
        Astronaut(
            name, heart_rate, spo2, temperature,
            astronaut_id=astronaut_id, gender=gender, date_of_birth=date_of_birth,
            age_years=age_years,
        )
        for astronaut_id, name, gender, date_of_birth, age_years, heart_rate, spo2, temperature in rows
    ]
