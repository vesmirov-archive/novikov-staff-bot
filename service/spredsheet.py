import datetime
import json


START_DATE = datetime.date(2021, 1, 1)
ROW_SHIFT = 3

with open('employees.json', 'r') as file:
    EMPLOYEES = json.loads(file.read())


def write_KPI_to_google_sheet(manager, sheet_key, page_id,
                              user_id, position, values):
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


def get_KPI_from_google_sheet(manager, sheet_key, page_id):
    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    data = {}
    for category in CATEGORIES_READ:
        data[category] = {}
        for value in CATEGORIES_READ[category]:
            cell = CATEGORIES_READ[category][value] + row
            content = page.get_value(cell)
            data[category].update({value: content})
    return data


def check_if_already_filled(manager, sheet_key, page_id, user_id, position):
    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)
    
    cells = map(
        lambda x: x + row,
        EMPLOYEES['подразделения'][position]['сотрудники'][user_id]['KPI'].values()  # noqa
    )
    for cell in cells:
        value = page.get_value(cell)
        if not value:
            return False
    return True


def get_daily_statistic(manager, sheet_key, page_id):
    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    values = {}
    for name, column in EMPLOYEES['сводка']['KPI'].items():
        values[name] = page.get_value(column + row)
    return values


def get_recipients_list():
    return EMPLOYEES['рассылка'].values()
