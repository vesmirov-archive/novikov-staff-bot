from datetime import date
from typing import Union, Optional

from handlers.utils import get_actual_row_for_section
from sheets.tools import get_cells_values
from settings import settings


def get_user_statistic_for_today(
        user_id: str,
        filter_by_section: Optional[str] = None,
) -> dict[str, Union[str, dict[str, str]]]:
    """
    TODO

    Return value sample:
    {
        '0': {'name': 'statistic_item_1', 'section': 'first_section_name', 'value': 1},
        '1': {'name': 'statistic_item_2', 'section': 'first_section_name', 'value': 2},
        '2': {'name': 'statistic_item_3', 'section': 'second_section_name', 'value': 3},
        ...
    }
    """

    result = {}

    columns_per_section = {}
    for item_number, item_data in settings.config['employees'][user_id]['statistics'].items():
        if filter_by_section and item_data['section'] != filter_by_section:
            continue
        columns_per_section.setdefault(item_data['section'], []).append(item_data['column'])
        result[item_number] = {
            'name': item_data['name'],
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


def get_statistic_for_today(filter_by_section: Optional[str] = None) -> dict[str, dict[str, dict]]:
    """
    TODO

    Return value sample:
    {
        'first_section_name': {
            'per_employee': {
                'statistic_item_1': [
                    ('First User', '1'),
                    ('Second User', '1'),
                ],
                'statistic_item_2': [
                    ('First User', '1'),
                ],
                'statistic_item_3': [
                    ('First User', '1'),
                    ('Second User', '1'),
                    ('Third User', '1')
                ],
            },
            'total': [
                ('statistic_item_1', '2'),
                ('statistic_item_2', '1'),
                ('statistic_item_3', '3'),
            ]
        },
        'second_section_name': {
        ...
    }
    """

    weekday_today = date.today().weekday()
    result = {}

    for user_id, user_data in settings.config['employees'].items():
        if not user_data['statistics']:
            continue

        user_statistic = get_user_statistic_for_today(
            user_id=user_id,
            filter_by_section=filter_by_section if filter_by_section else None,
        )
        for item_data in user_statistic.values():
            section_name = settings.config['sections'][item_data['section']]['name']
            result.setdefault(
                section_name, {},
            ).setdefault(
                'per_employee', {},
            ).setdefault(
                item_data['name'], [],
            ).append(
                (f'{user_data["firstname"]} {user_data["lastname"]}', item_data['value']),
            )

    # get total
    for section, data in settings.config['sections'].items():
        section_name = settings.config['sections'][section]['name']

        if filter_by_section and section != filter_by_section:
            continue

        names, columns = [], []
        for statistic_item in data['statistics']['period']['day'].values():
            names.append(statistic_item['name'])
            columns.append(statistic_item['column'])

        values = get_cells_values(
            table_id=data['google']['table'],
            sheet_id=data['google']['sheet'],
            columns=columns,
            row=str(get_actual_row_for_section(section))
        )
        total_data = list(zip(names, values))

        result[section_name].update({'total': total_data})

    return result
