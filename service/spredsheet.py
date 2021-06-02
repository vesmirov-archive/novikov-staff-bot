import datetime
import json


START_DATE = datetime.date(2021, 1, 1)
ROW_SHIFT = 3

with open('employees.json', 'r') as file:
    EMPLOYEES = json.loads(file.read())


def write_KPI_to_google_sheet(manager, sheet_key, page_id, data):
    sheet = manager.open_by_key(sheet_key)
    page = sheet.worksheet('id', page_id)
    diff = datetime.date.today() - START_DATE
    row = str(diff.days + ROW_SHIFT)

    for name, value in data.items():
        if name in CATEGORIES_WRITE:
            cell = CATEGORIES_WRITE[name] + row
            page.update_value(cell, value)


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
