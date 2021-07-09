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
    query = page.get_values(cells[0], cells[-1])

    return dict(zip(desc, query[0]))


def write_KPI_to_google_sheet(manager, sheet_key, page_id,
                              user_id, department, position, values):
    """Update specific cells with given values (KPI)"""

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
    except KeyError as e:
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
    col = CONFIG['сводка']['делопроизводство']['KPI неделя']['исков подано']

    page.update_value(col + row, value)

    # for future exeptions
    return True


def get_daily_statistic(manager, sheet_key, page_id, department):
    """Get all values for today"""

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
    """Get every employee value for today"""

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
    """Get all values for the week"""

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


def get_recipients_list():
    """Get users, which must be notificated with statistic"""

    return CONFIG['рассылка'].values()


def check_if_already_filled(page, user_id, department, position, row):
    """Check specific worksheet cells if they already has been filled"""

    values = google_query_booster(
        page,
        CONFIG['подразделения'][department][position]['сотрудники'][str(user_id)]['KPI'],  # noqa
        row
    )

    for value in values:
        if not value:
            return False

    return True


def get_leaders_from_google_sheet(manager, sheet_key, page_id, department):
    """Find leaders among all emoloyees"""

    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    score = google_query_booster(
        page,
        CONFIG['сводка'][department]['молодцы']['баллы'],
        row
    )

    for key in score:
        score[key] = int(score[key])
    max_points = max(score.values())

    leaders = []
    if max_points:
        for name, points in score.items():
            if points == max_points:
                leaders.append(name)
    return leaders
