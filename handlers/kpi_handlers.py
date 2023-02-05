from typing import Union

from settings import settings
from sheets.manager import manager

from datetime import date


def prepare_kpi_keys_and_questions(employee_id: Union[int, str]) -> tuple[list[str], list[str]]:
    """TODO"""

    employee_id = str(employee_id)
    day_of_the_week_today = date.weekday(date.today())
    kpi_keys, kpi_questions = [], []

    employee_kpi_data = settings.config['employees'][employee_id]['kpi']
    if employee_kpi_data:
        for kpi_key, kpi_data in settings.config['employees'][employee_id]['kpi'].items():
            if day_of_the_week_today in kpi_data['schedule']:
                kpi_keys.append(kpi_key)
                kpi_questions.append(kpi_data['question'])

    return kpi_keys, kpi_questions


def send_kpi_to_google(employee_id: str, kpi_values: tuple[str, str]) -> bool:
    ...

