from datetime import date
from typing import Union, Optional, Any

from settings import settings
from sheets.tools import update_cell_value, get_cells_values, get_cell_value
from sheets.utils import get_actual_row_for_section


def get_user_statistics_for_today(
        user_id: str,
        filter_by_section_id: Optional[str] = None,
) -> dict[str, Union[str, dict[str, str]]]:
    """
    Extracts statistics for the specified user according to the configuration file.

    :user_id: id of the user which statistics data should be extracted
    :filter_by_section_id: section id which should be filtered

    Return value sample:
    {
        '0': {'item_name': 'statistic_item_1', 'section': 'first_section_name', 'value': 1},
        '1': {'item_name': 'statistic_item_2', 'section': 'first_section_name', 'value': 2},
        '2': {'item_name': 'statistic_item_3', 'section': 'second_section_name', 'value': 3},
        ...
    }
    """

    result = {}

    columns_per_section = {}
    for item_number, item_data in settings.config['employees'][user_id]['statistics'].items():
        if filter_by_section_id and item_data['section'] != filter_by_section_id:
            continue
        columns_per_section.setdefault(item_data['section'], []).append(item_data['column'])
        result[item_number] = {
            'item_name': item_data['name'],
            'section': item_data['section'],
        }

    for section, columns in columns_per_section.items():
        section_google_data = settings.config['sections'][section]['google']
        section_values = get_cells_values(
            table_id=section_google_data['table'],
            sheet_id=section_google_data['sheet'],
            columns=columns,
            row=str(get_actual_row_for_section(section))
        )
        section_values_index = 0
        for item_number in result.keys():
            if result[item_number]['section'] == section:
                result[item_number].update({'value': section_values[section_values_index]})
                section_values_index += 1

    return result


def get_statistic_for_today(filter_by_section_id: Optional[str] = None) -> dict[str, Any]:
    """
    TODO

    Return value sample:
    {
        'first_section_name': {
            'total': [
                ('statistic_item_1', '2'),
                ('statistic_item_2', '3'),
                ('statistic_item_3', '1'),
                ('statistic_item_4', '1'),
                ('statistic_item_5', '1'),
            ],
            'per_employee': [
                {
                    'full_name': 'Full Name 1',
                    'statistics': [
                        ('statistic_item_1', '1'),
                        ('statistic_item_2', '1')
                    ],
                },
                {
                    'full_name': 'Full Name 2',
                    'statistics': [
                        ('statistic_item_1', '1'),
                        ('statistic_item_2', '2'),
                    ],
                ),
                }
                    'full_name': 'Full Name 3',
                    'statistics': [
                        ('statistic_item_3', '1'),
                        ('statistic_item_4', '1'),
                        ('statistic_item_5', '1'),
                    ],
                },
            ],
        },
        'second_section_name': {
        ...
    }
    """

    result = {}

    # fill with total values
    for section_id, data in settings.config['sections'].items():
        section_name = settings.config['sections'][section_id]['name']

        if filter_by_section_id and section_id != filter_by_section_id:
            continue

        items_names, sheet_columns = [], []
        for statistic_item in data['statistics']['period']['day'].values():
            items_names.append(statistic_item['name'])
            sheet_columns.append(statistic_item['column'])

        values = get_cells_values(
            table_id=data['google']['table'],
            sheet_id=data['google']['sheet'],
            columns=sheet_columns,
            row=str(get_actual_row_for_section(section_id))
        )
        total_data = list(zip(items_names, values))

        result.setdefault(section_name, {}).update({'total': total_data})

        users_results = []
        for user_id, user_data in settings.config['employees'].items():
            if not user_data['statistics']:
                continue

            user_statistics = get_user_statistics_for_today(user_id=user_id, filter_by_section_id=section_id)

            if not user_statistics.values():
                continue

            user_result = {
                'full_name': f'{user_data["firstname"]} {user_data["lastname"]}',
                'statistics': [(item['item_name'], item['value']) for item in user_statistics.values()],
            }
            users_results.append(user_result)

        result[section_name]['per_employee'] = users_results

    return result


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
            value=value_to_update,
            column=kpi_item['column'],
            row=str(get_actual_row_for_section(kpi_item['section'])),
        )


def get_key_values() -> dict[str, dict[str, tuple[str, str, str]]]:
    """
    TODO

    Return value sample:
    {
        '0': {
            'name': 'key_value_item_1',
            'values': [(period_1, actual_1, None), (period_2, actual_2, planned_2), ...]
        },
        '1': {
            'name': 'key_value_item_2',
            'values': [(period_1, actual_1, None), (period_2, actual_2, planned_2), ...]
        },
        '2': {
            'name': 'key_value_item_3',
            'values': [(period_1, actual_1, None), (period_2, actual_2, planned_2), ...]
        },
        ...
    }
    """

    result = {}
    for item_id, key_value_data in settings.config['other']['key-values']['items'].items():
        result[item_id] = {'name': key_value_data['name'], 'values': []}

        for period_data in key_value_data['statistics']['period'].values():
            period = period_data['name']
            actual = get_cell_value(
                table_id=settings.config['other']['key-values']['google']['table'],
                sheet_id=settings.config['other']['key-values']['google']['sheet'],
                cell=period_data['cells']['actual'],
            )
            planned = get_cell_value(
                table_id=settings.config['other']['key-values']['google']['table'],
                sheet_id=settings.config['other']['key-values']['google']['sheet'],
                cell=period_data['cells']['planned'],
            ) if period_data['cells']['planned'] else None
            result[item_id]['values'].append((period, actual, planned))

    return result

