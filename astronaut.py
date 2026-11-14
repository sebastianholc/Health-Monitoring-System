from datetime import datetime


class Astronaut:
    id = 0
    name = "Astronaut"
    gender = "Male"
    date_of_birth = "29/05/2003"
    heart_rate = 0
    spo2 = 0
    temperature = 0

    def __init__(self, name, heart_rate, spo2, temperature):
        self.name = name
        self.heart_rate = heart_rate
        self.spo2 = spo2
        self.temperature = temperature

    def age(self, current_time="14/11/2026"):
        dob = datetime.strptime(self.date_of_birth, "%d/%m/%Y")
        curr = datetime.strptime(current_time, "%d/%m/%Y")

        years = curr.year - dob.year
        # Jeśli w bieżącym roku nie było jeszcze urodzin, odejmujemy 1 rok
        if (curr.month, curr.day) < (dob.month, dob.day):
            years -= 1

        return years