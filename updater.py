"""
    Notifies users through a specific way (flags):
    '-c day-sales' -- save current day values
    '-c week-sales' -- save current week values
    '-c week-law' -- save current week values
"""

import argparse
import json

from dotenv import dotenv_values
import pygsheets

from service import spredsheet

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', dest='config')
args = parser.parse_args()

env = dotenv_values('.env')

with open('config.json', 'r') as file:
    CONFIG = json.loads(file.read())

TOKEN = env.get('TELEGRAM_STAFF_TOKEN')

CLIENT_SECRET_FILE = env.get('CLIENT_SECRET_FILE')


def save_plan_values(manager, department, period):
    """
        Save plan for department
    """

    for position, employees in CONFIG['подразделения'][department].items():
        for user_id, values in employees['сотрудники'].items():
            spredsheet.save_current_plan_to_google_sheet(
                manager,
                CONFIG['google']['tables']['план']['table'],
                CONFIG['google']['tables']['план']['sheets'][department],
                user_id,
                department,
                position,
                period
            )
            spredsheet.remove_old_plan_from_google_sheet(
                manager,
                CONFIG['google']['tables']['план']['table'],
                CONFIG['google']['tables']['план']['sheets'][department],
                user_id,
                department,
                position,
                period
            )


def main():
    """Notification manager"""

    manager = pygsheets.authorize(service_account_file=CLIENT_SECRET_FILE)

    if args.config == 'day-sales':
        save_plan_values(manager, 'продажи', 'день')
    elif args.config == 'week-sales':
        save_plan_values(manager, 'продажи', 'неделя')
    elif args.config == 'week-law':
        save_plan_values(manager, 'делопроизводство', 'неделя')


if __name__ == '__main__':
    main()
