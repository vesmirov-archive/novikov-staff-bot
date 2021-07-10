"""
    Notifies users through a specific way (flags):
    '-c day' -- send day statistic
    '-c week' -- send week statistic
    '-c kpi-first' -- send first kpi notification
    '-c kpi-second' -- send second kpi notification
    '-c lawsuits' -- send lawsuits notification
"""

import argparse
import json

import telebot
import pygsheets
from dotenv import dotenv_values

from service import db
from service import spredsheet

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', dest='config')
args = parser.parse_args()

env = dotenv_values('.env')

with open('config.json', 'r') as file:
    CONFIG = json.loads(file.read())

# telegram
TOKEN = env.get('TELEGRAM_STAFF_TOKEN')

# google
CLIENT_SECRET_FILE = env.get('CLIENT_SECRET_FILE')

# messages
KPI_MESSAGE = (
    'Привет! Рабочий день закончен, самое время заняться своими делами :)\n'
    'Напоследок, пожалуйста, пришли мне свои цифры за сегодня, '
    'нажав кнопку "показатели \U0001f3af"'
)
KPI_SECOND_MESSAGE = (
    'Через 30 минут руководству будет отправлена '
    'сводка за день, а я так и не получил твоих цифр. Поспеши!'
)
FAIL_MESSAGE = (
    'Я попытался с тобой связаться, '
    'но кажется тебя не добавили в мой список :(\n'
    'Пожалуйста, сообщи об ошибке ответственному лицу'
)
LAWSUITS_MESSAGE = (
    'Наконец-то конец рабочей недели! :)\n'
    'Пожалуйста, проверь на актуальность количество поданных '
    'исков за неделю.\n\nВнести данные можно через кнопку "иски \U0001f5ff"'
)


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
        needed_employee = spredsheet.check_employees_values_for_fullness(
            manager,
            CONFIG['google']['table'],
            CONFIG['google']['sheet'][department],
            department
        )
        for employee_id in needed_employee:
            print(employee_id)
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
            CONFIG['google']['table'],
            CONFIG['google']['sheet'][department],
            department
        )
        departments_statistic.append(day)

    department_leaders = {}
    for department in departments_tracked:
        leaders = spredsheet.get_leaders_from_google_sheet(
            manager,
            CONFIG['google']['table'],
            CONFIG['google']['sheet'][department],
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
            CONFIG['google']['table'],
            CONFIG['google']['sheet'][department],
            department
        )
        departments_statistic.append(week)

    for recipient_id in CONFIG['рассылка'].values():
        bot.send_message(recipient_id, 'Итоги недели \U0001f5d3')
        for values in departments_statistic:
            result = []
            result.extend([f'{k}: {v}' for k, v in values.items()])
            bot.send_message(recipient_id, '\n'.join(result))


def remind_to_send_lawsuits(bot):
    """
        Notifications abount sending lawsuits
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


def main():
    """
        Notification manager
    """

    bot = telebot.TeleBot(TOKEN)
    manager = pygsheets.authorize(service_account_file=CLIENT_SECRET_FILE)

    if args.config == 'day':
        send_daily_results(bot, manager)
    elif args.config == 'week':
        send_weekly_results(bot, manager)
    elif args.config == 'kpi-first':
        remind_to_send_kpi(bot, manager)
    elif args.config == 'kpi-second':
        remind_to_send_kpi(bot, manager, True)
    elif args.config == 'lawsuits':
        remind_to_send_lawsuits(bot)


if __name__ == '__main__':
    main()
