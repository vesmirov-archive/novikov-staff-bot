from typing import Union

from settings import settings
from sheets.tools import update_google_sheet_cell

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


def update_employee_kpi(employee_id: Union[int, str], kpi_values: list[tuple[str, str]]) -> None:
    """TODO"""

    employee_id = str(employee_id)
    days_diff = date.today() - date.fromisoformat(settings.config['start_date'])
    for kpi_key, value_to_update in kpi_values:
        kpi_item = settings.config['employees'][employee_id]['kpi'][kpi_key]
        section_google_data = settings.config['sections'][kpi_item['section']]['google']

        update_google_sheet_cell(
            table_id=section_google_data['table'],
            sheet_id=section_google_data['sheet'],
            column=kpi_item['column'],
            row=str(days_diff.days + section_google_data['start_row']),
            value=value_to_update,
        )