import datetime
from logging import getLogger
from typing import Union, Iterable

from sheets.manager import manager
from settings import settings

START_DATE = datetime.date.fromisoformat(settings.config['start_date'])


logger = getLogger(__name__)

# def google_query_booster(page, values, row):
#     values = list(zip(values.keys(), values.values()))
#     values.sort(key=lambda x: (len(x[1]), x[1]))
#     desc = [k for k, _ in values]
#     cells = [(v + row) for _, v in values]
#
#     if not cells:
#         return {}
#
#     query = page.get_values(cells[0], cells[-1])
#     return dict(zip(desc, query[0]))


# for kpi_key, kpi_value in values.items():
#     section_google_data = settings.config['sections'][kpi_value['section']]['google']
#     table = google.manager.open_by_key(section_google_data['table'])
#     sheet = table.worksheet('id', section_google_data['sheet'])
#     cell = kpi_value['column'] + str(diff.days + section_google_data['start_row'])


def update_cell_value(
        table_id: str,
        sheet_id: str,
        column: str,
        row: str,
        value: str,
) -> None:
    """
    Updates the cell of specified Google sheets.
    """

    table = manager.client.open_by_key(table_id)
    sheet = table.worksheet('id', sheet_id)
    cell = column + row

    try:
        sheet.update_value(cell, value)
    except Exception:
        logger.exception(
            'Could not write data to the cell',
            extra={'table': table, 'sheet_id': sheet_id, 'cell': cell, 'value': value},
        )


def get_cell_value(
        table_id: str,
        sheet_id: str,
        column: str,
        row: str,
) -> Union[str, None]:
    """
    Get value from the specific cell
    """

    table = manager.client.open_by_key(table_id)
    sheet = table.worksheet('id', sheet_id)
    cell = column + row

    result = None
    try:
        result = sheet.get_value(cell)
    except Exception:
        logger.exception(
            'Could not get cell data from the sheet',
            extra={'table': table, 'sheet_id': sheet_id, 'cell': cell},
        )
    finally:
        return result


def get_cells_values(
        table_id: str,
        sheet_id: str,
        columns: Iterable[str],
        row: str,
) -> Union[list[tuple[str, str]], None]:
    """TODO"""

    table = manager.client.open_by_key(table_id)
    sheet = table.worksheet('id', sheet_id)
    cells = [(column + row, column + row) for column in columns]

    result = None
    try:
        result = tuple(map(lambda arr: arr[0][0], sheet.get_values_batch(cells)))
    except Exception:
        logger.exception(
            'Could not get cells data from the sheet',
            extra={'table': table, 'sheet_id': sheet_id, 'cells': cells},
        )
    finally:
        return result


# def save_current_plan_to_google_sheet(sheet_key, page_id, user_id,
#                                       department, position, period):
#     """
#         Save current period values in other cells
#     """
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#
#     plan = list(CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['планирование'][period]['текущая']['план'].values()) # noqa
#     fact = list(CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['планирование'][period]['текущая']['факт'].values()) # noqa
#     query = page.get_values(plan[0], fact[-1])
#
#     for row in query:
#         for idx in range(len(row)):
#             if row[idx] == '':
#                 row[idx] = '0'
#
#     cells = zip(
#         CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['планирование'][period]['предыдущая']['план'].values(), # noqa
#         query
#     )
#     for cell in cells:
#         page.update_values(cell[0], [cell[1]])
#
#
# def remove_old_plan_from_google_sheet(sheet_key, page_id, user_id,
#                                       department, position, period):
#     """
#         Remove old plan from cells
#     """
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#
#     cells = list(CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['планирование'][period]['текущая']['план'].values())  # noqa
#     for cell in cells:
#         page.clear(cell, cell)
#
#
# def write_lawsuits_to_google_sheet(sheet_key, page_id, value):
#     """
#         Update specific cells with given values (lawsuits)
#     """
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#     diff = datetime.date.today() - START_DATE
#     row = str(diff.days - datetime.date.today().weekday() + ROW_SHIFT)
#     col = CONFIG['сводка']['делопроизводство']['KPI неделя']['исков подано']
#
#     page.update_value(col + row, value)
#
#     # for future exeptions
#     return True
#
#
# def write_income_to_google_sheet(sheet_key, page_id, value):
#     """
#         Update specific cells with given values (income)
#     """
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#     diff = datetime.date.today() - START_DATE
#     row = str(diff.days + ROW_SHIFT)
#     col = CONFIG['сводка']['руководство']['KPI день']['выручка']
#
#     page.update_value(col + row, value)
#
#     return True
#
#
# def get_daily_statistic(sheet_key, page_id, department):
#     """
#         Get all values for today
#     """
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#     diff = datetime.date.today() - START_DATE
#     row = str(diff.days + ROW_SHIFT)
#
#     values = google_query_booster(
#         page,
#         CONFIG['сводка'][department]['KPI день'],
#         row
#     )
#     return values
#
#
# def get_daily_detail_statistic(sheet_key, page_id, department):
#     """
#         Get every employee value for today
#     """
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#     diff = datetime.date.today() - START_DATE
#     row = str(diff.days + ROW_SHIFT)
#
#     employees = {}
#     for position, values in CONFIG['подразделения'][department].items():
#         employees[position] = {}
#         for employee in values['сотрудники'].values():
#             if employee['KPI']:
#                 full_name = employee['имя'] + ' ' + employee['фамилия']
#                 employees[position][full_name] = google_query_booster(
#                     page, employee['KPI'], row)
#     return employees
#
#
# def get_weekly_statistic(sheet_key, page_id, department):
#     """
#         Get all values for the week
#     """
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#     diff = datetime.date.today() - START_DATE
#     row = str(diff.days - datetime.date.today().weekday() + ROW_SHIFT)
#
#     values = google_query_booster(
#         page,
#         CONFIG['сводка'][department]['KPI неделя'],
#         row
#     )
#     return values
#
#
# def check_employees_values_for_fullness(sheet_key,
#                                         page_id, department):
#     """
#         Check specific worksheet cells if they already has been filled
#     """
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#     diff = datetime.date.today() - START_DATE
#     row = str(diff.days + ROW_SHIFT)
#
#     needed_employee = []
#     for position, values in CONFIG['подразделения'][department].items():
#         for employee_id, employee in values['сотрудники'].items():
#             employee_values = google_query_booster(
#                 page,
#                 employee['KPI'],
#                 row
#             )
#             for value in employee_values.values():
#                 if not value:
#                     needed_employee.append(employee_id)
#                     break
#     return needed_employee
#
#
# def check_employees_plan_for_fullness(sheet_key,
#                                       page_id, department, period):
#     """
#         Check specific worksheet cells if they already has been filled
#     """
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#
#     needed_employee = []
#     for position, values in CONFIG['подразделения'][department].items():
#         for employee_id, employee in values['сотрудники'].items():
#             try:
#                 for cell in employee['планирование'][period]['текущая']['план'].values():
#                     if not page.get_value(cell):
#                         needed_employee.append(employee_id)
#                         break
#             except KeyError:
#                 needed_employee
#     return needed_employee
#
#
# def get_leaders_from_google_sheet(sheet_key, page_id, department):
#     """
#         Find leaders among all emoloyees
#     """
#
#     leaders = []
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#     diff = datetime.date.today() - START_DATE
#     row = str(diff.days + ROW_SHIFT)
#
#     score = google_query_booster(
#         page,
#         CONFIG['сводка'][department]['молодцы']['баллы'],
#         row
#     )
#
#     if not score:
#         return leaders
#
#     for key in score:
#         score[key] = int(score[key])
#     max_points = max(score.values())
#
#     if max_points:
#         for name, points in score.items():
#             if points == max_points:
#                 leaders.append(name)
#     return leaders
#
#
# def get_general_motivation(sheet_key, page_id):
#     """
#         Get general motivation
#     """
#     motivation = {}
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#
#     for cat_name, periods in CONFIG['мотивация'].items():
#         motivation[cat_name] = {}
#         for period, cells in periods.items():
#             motivation[cat_name][period] = {
#                 'план': ''.join(page.get_value(cells['план']).split('\xa0')) if cells['план'] else 'нет',
#                 'факт': ''.join(page.get_value(cells['факт']).split('\xa0')) if cells['факт'] else 'нет',
#             }
#
#     return motivation
#
#
# def get_personal_motivation(sheet_key, page_id):
#     """
#         Get personal motivation
#     """
#     motivation = {}
#
#     sheet = google.manager.open_by_key(sheet_key)
#     page = sheet.worksheet('id', page_id)
#
#     for cat_name, employees in CONFIG['мотивация сотрудники'].items():
#         motivation[cat_name] = {}
#         for employee, periods in employees.items():
#             motivation[cat_name][employee] = {}
#             for period, cell in periods.items():
#                 motivation[cat_name][employee][period] = ''.join(page.get_value(cell).split('\xa0'))
#
#     return motivation
