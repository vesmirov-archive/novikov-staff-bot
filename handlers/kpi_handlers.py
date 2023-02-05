from settings import settings
from google import spredsheet

from datetime import date


def prepare_kpi_keys_and_questions(employee_id: str) -> tuple[list[str], list[str]]:
    """TODO"""

    day_of_the_week_today = date.weekday(date.today())
    kpi_keys, kpi_questions = [], []

    for kpi_key, kpi_data in settings.config['employees'][employee_id]['kpi'].items():
        if day_of_the_week_today in kpi_data['schedule']:
            kpi_keys.append(kpi_key)
            kpi_questions.append(kpi_data['question'])

    return kpi_keys, kpi_questions


def send_kpi_to_google(employee_id: str, kpi_values: tuple[str, str]) -> bool:
    ...

