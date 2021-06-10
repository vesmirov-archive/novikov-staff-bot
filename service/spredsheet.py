"""
    Google sheets module
"""

import datetime
import json


START_DATE = datetime.date(2021, 1, 1)
ROW_SHIFT = 3

with open('employees.json', 'r') as file:
    EMPLOYEES = json.loads(file.read())


def write_KPI_to_google_sheet(manager, sheet_key, page_id,
                              user_id, position, values):
    """Update specific cells with given values (KPI)"""

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    try:
        user_id = str(user_id)
        cols = map(
            lambda x: x + row,
            EMPLOYEES['подразделения'][position]['сотрудники'][user_id]['KPI'].values()  # noqa
        )
        cells = zip(cols, values)
    except KeyError:
        return False
    else:
        for cell in cells:
            page.update_value(cell[0], cell[1])
        return True


def write_lawsuits_to_google_sheet(manager, sheet_key, page_id, value):
    """Update specific cells with given values (lawsuits)"""

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days - datetime.date.today().weekday() + ROW_SHIFT)
    col = EMPLOYEES['сводка']['KPI неделя']['исков подано']

    page.update_value(col + row, value)

    # for future exeptions
    return True


def check_if_already_filled(manager, sheet_key, page_id, user_id, position):
    """Check specific worksheet cells if they already has been filled"""

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    cells = map(
        lambda x: x + row,
        EMPLOYEES['подразделения'][position]['сотрудники'][str(user_id)]['KPI'].values()  # noqa
    )
    for cell in cells:
        value = page.get_value(cell)
        if not value:
            return False
    return True


def get_daily_statistic(manager, sheet_key, page_id):
    """Get all values for today"""

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    values = {}
    for name, col in EMPLOYEES['сводка']['KPI день'].items():
        values[name] = page.get_value(col + row)
    return values


def get_daily_statistic_of_employee_in_division(
        manager,
        sheet_key,
        page_id,
        divisions=["делопроизводство", "исполнение"]
    ):
    """Get every employee value for today"""

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    values = {}
    for division in divisions:
        for employee in EMPLOYEES['подразделения'][division]['сотрудники'].values():
            full_name = employee['имя'] + ' ' + employee['фамилия']
            values[full_name] = {}
            for value, col in employee['KPI'].items():
                values[full_name][value] = page.get_value(col + row)
    values['Общее'] = get_daily_statistic(manager, sheet_key, page_id)
    
    return values
    


def get_weekly_statistic(manager, sheet_key, page_id):
    """Get all values for the week"""

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days - datetime.date.today().weekday() + ROW_SHIFT)

    values = {}
    for name, col in EMPLOYEES['сводка']['KPI неделя'].items():
        values[name] = page.get_value(col + row)
    return values


def get_recipients_list():
    """Get users, which must be notificated with statistic"""

    return EMPLOYEES['рассылка'].values()


def get_leaders_from_google_sheet(manager, sheet_key, page_id):
    """Find leaders among all emoloyees"""

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    people = {}
    for name, col in EMPLOYEES['сводка']['молодцы'].items():
        people[name] = int(page.get_value(col + row))

    leaders = []
    max_points = 0
    for points in people.values():
        if points > max_points:
            max_points = points

    if max_points:
        for name, points in people.items():
            if points == max_points:
                leaders.append(name)
    return leaders
