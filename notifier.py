"""
    Notifies users through a specific way (flags):
    '-c day' -- send day statistic
    '-c week' -- send week statistic
    '-c kpi-first' -- send first kpi notification
    '-c kpi-second' -- send second kpi notification
    '-c plan-day-first' -- send first day plan notification
    '-c plan-day-second' -- send second day plan notification
    '-c plan-week-first' -- send first week plan notification
    '-c plan-week-second' -- send second week plan notification
    '-c lawsuits' -- send lawsuits notification
"""

import argparse
import json

from dotenv import dotenv_values
import pygsheets
import telebot

from messages import (
    KPI_MESSAGE, 
    KPI_SECOND_MESSAGE,
    FAIL_MESSAGE,
    LAWSUITS_MESSAGE,
    INCOME_MESSAGE,
    DAY_PLAN_MESSAGE,
    DAY_PLAN_SECOND_MESSAGE,
    WEEK_PLAN_MESSAGE,
    WEEK_PLAN_SECOND_MESSAGE
)
from service import db
from service import spredsheet

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', dest='config')
args = parser.parse_args()

env = dotenv_values('.env')

with open('config.json', 'r') as file:
    CONFIG = json.loads(file.read())

TOKEN = env.get('TELEGRAM_STAFF_TOKEN')

CLIENT_SECRET_FILE = env.get('CLIENT_SECRET_FILE')

def remind_to_send_kpi(bot, manager, second=False):
    """
        Notifications abount sending KPI values
    """

    text = KPI_SECOND_MESSAGE if second else KPI_MESSAGE

    departments_tracked = []
    for department, positions in CONFIG['отслеживание'].items():
        tracked = list(filter(lambda x: x, positions.values()))
        if tracked:
            departments_tracked.append(department)

    for department in departments_tracked:
        needed_employees = spredsheet.check_employees_values_for_fullness(
            manager,
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets'][department],
            department
        )
        for employee_id in needed_employees:
            bot.send_message(employee_id, text)


def remind_to_send_plan(bot, manager, period, second=False):
    
    if period == 'день':
        text = DAY_PLAN_SECOND_MESSAGE if second else DAY_PLAN_MESSAGE
    else:
        text = WEEK_PLAN_SECOND_MESSAGE if second else WEEK_PLAN_MESSAGE
        

    departments_tracked = []
    for department, positions in CONFIG['отслеживание'].items():
        tracked = list(filter(lambda x: x, positions.values()))
        if tracked:
            departments_tracked.append(department)

    for department in departments_tracked:
        needed_employees = spredsheet.check_employees_plan_for_fullness(
            manager,
            CONFIG['google']['tables']['план']['table'],
            CONFIG['google']['tables']['план']['sheets'][department],
            department,
            period
        )
        for employee_id in needed_employees:
            bot.send_message(employee_id, text)


def send_daily_results(bot, manager):
    """
        Sends daily results
    """

    departments_tracked = []
    for department, positions in CONFIG['отслеживание'].items():
        tracked = list(filter(lambda x: x, positions.values()))
        if tracked:
            departments_tracked.append(department)

    departments_statistic = []
    for department in departments_tracked:
        day = spredsheet.get_daily_detail_statistic(
            manager,
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets'][department],
            department
        )
        departments_statistic.append(day)

    department_leaders = {}
    for department in departments_tracked:
        leaders = spredsheet.get_leaders_from_google_sheet(
            manager,
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets'][department],
            department
        )
        department_leaders.update({department: leaders})

    for recipient_id in CONFIG['рассылка'].values():
        bot.send_message(recipient_id, 'Итоги дня \U0001f4ca')

        for values in departments_statistic:
            result = []
            for position, employees in values.items():
                employees_result = []
                for employee, values in employees.items():
                    employees_result.append(f'\n\U0001F464 {employee}:\n')
                    employees_result.append(
                        '\n'.join([f'{k}: {v}' for k, v in values.items()]))
                result.append(f'\n\n\U0001F53D {position.upper()}')
                result.append('\n'.join(employees_result))
            bot.send_message(recipient_id, '\n'.join(result))

        bot.send_message(recipient_id, 'Красавчики дня \U0001F3C6')

        leaders = []
        for department, values in department_leaders.items():
            if department == 'делопроизводство':
                if values:
                    leaders.append(
                        f'\U0001f38a {department.capitalize()}: ' +
                        ', '.join(values)
                    )
                else:
                    leaders.append(
                        f'\U0001f5ff {department.capitalize()}: ' +
                        'Красавчиков дня нет'
                    )
        bot.send_message(recipient_id, '\n\n'.join(leaders))


def send_weekly_results(bot, manager):
    """
        Sends weekly results
    """

    departments_tracked = []
    for department, positions in CONFIG['отслеживание'].items():
        tracked = list(filter(lambda x: x, positions.values()))
        if tracked:
            departments_tracked.append(department)

    departments_statistic = []
    for department in departments_tracked:
        week = spredsheet.get_weekly_statistic(
            manager,
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets'][department],
            department
        )
        departments_statistic.append(week)

    for recipient_id in CONFIG['рассылка'].values():
        bot.send_message(recipient_id, 'Итоги недели \U0001f5d3')
        for values in departments_statistic:
            result = []
            result.extend([f'{k}: {v}' for k, v in values.items()])
            bot.send_message(recipient_id, '\n'.join(result))


def send_department_daily_results(bot, manager, cursor, department):
    """
        Send department daily results to employees
    """

    ids = db.return_ids_of_users_from(cursor, department)

    kpi_daily = spredsheet.get_daily_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department
    )

    result = ['Статистика за день \U0001f4c6\n']
    result.extend([f'{k}: {v}' for k, v in kpi_daily.items()])

    for id in ids:
        bot.send_message(id, '\n'.join(result))

    result = ['Статистика по сотрудникам \U0001F465\n']

    kpi_daily_detail = spredsheet.get_daily_detail_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department
    )
    for position, employees in kpi_daily_detail.items():
        employees_result = []
        if employees:
            for employee, values in employees.items():
                employees_result.append(f'\n\U0001F464 {employee}:\n')
                employees_result.append(
                    '\n'.join([f'{k}: {v}' for k, v in values.items()]))
            result.append(f'\n\n\U0001F53D {position.upper()}')
            result.append('\n'.join(employees_result))

    for id in ids:
        bot.send_message(id, '\n'.join(result))


def send_department_weekly_results(bot, manager, cursor, department):
    """
        Send department daily results to employees
    """

    ids = db.return_ids_of_users_from(cursor, department)

    kpi_daily = spredsheet.get_weekly_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department
    )

    result = ['Статистика за неделю \U0001f5d3\n']
    result.extend([f'{k}: {v}' for k, v in kpi_daily.items()])

    for id in ids:
        bot.send_message(id, '\n'.join(result))


def remind_to_send_lawsuits(bot):
    """
        Notifications abont sending lawsuits
    """

    ids = map(str, CONFIG['иски'].values())

    connect, cursor = db.connect_database(env)
    cursor.execute(
        "SELECT user_id FROM employees "
        f"WHERE user_id IN ({', '.join(ids)})"
    )
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]
        bot.send_message(user_id, LAWSUITS_MESSAGE)


def remind_to_send_income(bot):
    """
        Notifications abont sending income
    """

    ids = map(str, CONFIG['выручка'].values())

    connect, cursor = db.connect_database(env)
    cursor.execute(
        "SELECT user_id FROM employees "
        f"WHERE user_id IN ({', '.join(ids)})"
    )
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]
        bot.send_message(user_id, INCOME_MESSAGE)


def main():
    """
        Notification manager
    """

    bot = telebot.TeleBot(TOKEN)
    manager = pygsheets.authorize(service_account_file=CLIENT_SECRET_FILE)
    connect, cursor = db.connect_database(env)

    if args.config == 'day':
        send_daily_results(bot, manager)
    elif args.config == 'day-law':
        send_department_daily_results(bot, manager, cursor, 'делопроизводство')
    elif args.config == 'day-sales':
        send_department_daily_results(bot, manager, cursor, 'продажи')
    elif args.config == 'week':
        send_weekly_results(bot, manager)
    elif args.config == 'week-law':
        send_department_weekly_results(bot, manager, cursor, 'делопроизводство')
    elif args.config == 'week-sales':
        send_department_weekly_results(bot, manager, cursor, 'продажи')
    elif args.config == 'week-head':
        send_department_weekly_results(bot, manager, cursor, 'руководство')
    elif args.config == 'kpi-first':
        remind_to_send_kpi(bot, manager)
    elif args.config == 'kpi-second':
        remind_to_send_kpi(bot, manager, True)
    elif args.config == 'plan-day-first':
        remind_to_send_plan(bot, manager, 'день')
    elif args.config == 'plan-day-second':
        remind_to_send_plan(bot, manager, 'день', True)
    elif args.config == 'plan-week-first':
        remind_to_send_plan(bot, manager, 'неделя')
    elif args.config == 'plan-week-second':
        remind_to_send_plan(bot, manager, 'неделя', True)
    elif args.config == 'lawsuits':
        remind_to_send_lawsuits(bot)
    elif args.config == 'income':
        remind_to_send_income(bot)

    connect.close()

if __name__ == '__main__':
    main()
