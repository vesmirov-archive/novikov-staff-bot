from datetime import date
from typing import Union

from handlers.sheets.utils import get_actual_row_for_section
from settings import settings
from sheets.tools import update_cell_value


def prepare_kpi_keys_and_questions(employee_id: Union[int, str]) -> tuple[list[str], list[str]]:
    """TODO"""

    employee_id = str(employee_id)
    day_of_the_week_today = date.weekday(date.today())
    kpi_keys, kpi_questions = [], []

    employee_kpi_data = settings.config['employees'][employee_id]['statistics']
    if employee_kpi_data:
        for kpi_key, kpi_data in settings.config['employees'][employee_id]['statistics'].items():
            if day_of_the_week_today in kpi_data['schedule']:
                kpi_keys.append(kpi_key)
                kpi_questions.append(kpi_data['question'])

    return kpi_keys, kpi_questions


def update_employee_kpi(employee_id: Union[int, str], kpi_values: list[tuple[str, str]]) -> None:
    """TODO"""

    employee_id = str(employee_id)
    for kpi_key, value_to_update in kpi_values:
        kpi_item = settings.config['employees'][employee_id]['statistics'][kpi_key]
        section_google_data = settings.config['sections'][kpi_item['section']]['google']

        update_cell_value(
            table_id=section_google_data['table'],
            sheet_id=section_google_data['sheet'],
            column=kpi_item['column'],
            row=str(get_actual_row_for_section(kpi_item['section'])),
            value=value_to_update,
        )
