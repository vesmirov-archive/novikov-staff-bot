"""
    Google sheets module
"""

import datetime
import json


START_DATE = datetime.date(2021, 1, 1)
ROW_SHIFT = 3

with open('config.json', 'r') as file:
    CONFIG = json.loads(file.read())


def google_query_booster(page, values, row):
    values = list(zip(values.keys(), values.values()))
    values.sort(key=lambda x: (len(x[1]), x[1]))
    desc = [k for k, _ in values]
    cells = [(v + row) for _, v in values]

    if not cells:
        return {}

    query = page.get_values(cells[0], cells[-1])
    return dict(zip(desc, query[0]))


def write_KPI_to_google_sheet(manager, sheet_key, page_id,
                              user_id, department, position, values):
    """
        Update specific cells with given values (KPI)
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    try:
        user_id = str(user_id)
        cols = map(
            lambda x: x + row,
            CONFIG['подразделения'][department][position]['сотрудники'][user_id]['KPI'].values()  # noqa
        )
        cells = zip(cols, values)
    except KeyError:
        return False
    else:
        for cell in cells:
            page.update_value(cell[0], cell[1])
        return True


def write_plan_to_google_sheet(manager, sheet_key, page_id, user_id,
                               department, position, period, values):
    """
        Update specific cells with given values (plan)
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)

    try:
        cells = zip(CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['планирование'][period]['текущая']['план'].values(), values)  # noqa
    except KeyError:
        return False
    for cell in cells:
        page.update_value(cell[0], cell[1])
    return True


def save_current_plan_to_google_sheet(manager, sheet_key, page_id, user_id,
                                      department, position, period):
    """
        Save current period values in other cells
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)

    plan = list(CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['планирование'][period]['текущая']['план'].values())  # noqa
    fact = list(CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['планирование'][period]['текущая']['факт'].values())  # noqa
    query = page.get_values(plan[0], fact[-1])

    for row in query:
        for idx in range(len(row)):
            if row[idx] == '':
                row[idx] = '0'

    cells = zip(
        CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['планирование'][period]['предыдущая']['план'].values(),  # noqa
        query
    )
    for cell in cells:
        page.update_values(cell[0], [cell[1]])


def remove_old_plan_from_google_sheet(manager, sheet_key, page_id, user_id,
                                      department, position, period):
    """
        Remove old plan from cells
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)

    cells = list(CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['планирование'][period]['текущая']['план'].values())  # noqa
    for cell in cells:
        page.clear(cell, cell)


def write_lawsuits_to_google_sheet(manager, sheet_key, page_id, value):
    """
        Update specific cells with given values (lawsuits)
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days - datetime.date.today().weekday() + ROW_SHIFT)
    col = CONFIG['сводка']['делопроизводство']['KPI неделя']['исков подано']

    page.update_value(col + row, value)

    # for future exeptions
    return True


def write_income_to_google_sheet(manager, sheet_key, page_id, value):
    """
        Update specific cells with given values (income)
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)
    col = CONFIG['сводка']['руководство']['KPI день']['выручка']

    page.update_value(col + row, value)

    return True


def get_daily_statistic(manager, sheet_key, page_id, department):
    """
        Get all values for today
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    values = google_query_booster(
        page,
        CONFIG['сводка'][department]['KPI день'],
        row
    )
    return values


def get_daily_detail_statistic(manager, sheet_key, page_id, department):
    """
        Get every employee value for today
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    employees = {}
    for position, values in CONFIG['подразделения'][department].items():  # noqa
        employees[position] = {}
        for employee in values['сотрудники'].values():
            if employee['KPI']:
                full_name = employee['имя'] + ' ' + employee['фамилия']
                employees[position][full_name] = google_query_booster(
                    page, employee['KPI'], row)
    return employees


def get_weekly_statistic(manager, sheet_key, page_id, department):
    """
        Get all values for the week
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days - datetime.date.today().weekday() + ROW_SHIFT)

    values = google_query_booster(
        page,
        CONFIG['сводка'][department]['KPI неделя'],
        row
    )
    return values


def check_employees_values_for_fullness(manager, sheet_key,
                                        page_id, department):
    """
        Check specific worksheet cells if they already has been filled
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    needed_employee = []
    for position, values in CONFIG['подразделения'][department].items():
        for employee_id, employee in values['сотрудники'].items():
            employee_values = google_query_booster(
                page,
                employee['KPI'],
                row
            )
            for value in employee_values.values():
                if not value:
                    needed_employee.append(employee_id)
                    break
    return needed_employee


def check_employees_plan_for_fullness(manager, sheet_key,
                                      page_id, department, period):
    """
        Check specific worksheet cells if they already has been filled
    """

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    needed_employee = []
    for position, values in CONFIG['подразделения'][department].items():
        for employee_id, employee in values['сотрудники'].items():
            try:
                for cell in employee['планирование'][period]['текущая']['план'].values():
                    if not page.get_value(cell):
                        needed_employee.append(employee_id)
                        break
            except KeyError:
                needed_employee
    return needed_employee


def get_leaders_from_google_sheet(manager, sheet_key, page_id, department):
    """
        Find leaders among all emoloyees
    """

    leaders = []

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    score = google_query_booster(
        page,
        CONFIG['сводка'][department]['молодцы']['баллы'],
        row
    )

    if not score:
        return leaders

    for key in score:
        score[key] = int(score[key])
    max_points = max(score.values())

    if max_points:
        for name, points in score.items():
            if points == max_points:
                leaders.append(name)
    return leaders


def get_general_motivation(manager, sheet_key, page_id):
    """
        Get general motivation
    """
    motivation = {}

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)

    for cat_name, periods in CONFIG['мотивация'].items():
        motivation[cat_name] = {}
        for period, cells in periods.items():
            motivation[cat_name][period] = {
                'план': ''.join(page.get_value(cells['план']).split('\xa0')) if cells['план'] else 'нет',
                'факт': ''.join(page.get_value(cells['факт']).split('\xa0')) if cells['факт'] else 'нет',
            }

    return motivation


def get_personal_motivation(manager, sheet_key, page_id, person_id):
    """
        Get personal motivation
    """
    motivation = {}

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
