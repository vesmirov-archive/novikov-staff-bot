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

with open('employees.json', 'r') as file:
    EMPLOYEES = json.loads(file.read())

# telegram
TOKEN = env.get('TELEGRAM_STAFF_TOKEN')
CHAT = env.get('TELEGRAM_CHAT_ID')

# google
SHEET_KEY = env.get('SHEET_KEY')
WORKSHEET_ID = env.get('WORKSHEET_STAFF_ID')
CLIENT_SECRET_FILE = env.get('CLIENT_SECRET_FILE')

# messages
KPI_MESSAGE = (
    'Привет {}! Рабочий день закончен, самое время заняться своими делами :)\n'
    'Напоследок, пожалуйста, пришли мне свои цифры за сегодня, нажав /kpi'
)
KPI_SECOND_MESSAGE = (
    '{}, через 30 минут руководству будет отправлена '
    'сводка за день, а я так и не получил твоих цифр. Поспеши!'
)
FAIL_MESSAGE = (
    'Я попытался с тобой связаться, '
    'но кажется тебя не добавили в мой список :(\n'
    'Пожалуйста, сообщи об ошибке ответственному лицу'
)
LAWSUITS_MESSAGE = (
    '{}, наконец-то конец рабочей недели! :)\n'
    'Пожалуйста, проверь на актуальность количество поданных '
    'исков за неделю.\n\nВнести данные можно через /lawsuits'
)

# employees with next positions will be notified
TRACKED_POSITIONS = [
    'делопроизводство',
    'исполнение'
]


def remind_to_send_kpi(bot, manager, second=False):
    """Notifications abount sending KPI values"""

    connect, cursor = db.connect_database(env)
    cursor.execute("SELECT user_id, position, firstname FROM employees")
    users = cursor.fetchall()

    text = KPI_SECOND_MESSAGE if second else KPI_MESSAGE

    for user in users:
        if user[1] not in TRACKED_POSITIONS:
            continue

        try:
            filled = spredsheet.check_if_already_filled(
                manager, SHEET_KEY, WORKSHEET_ID, user[0], user[1])
            if not filled:
                bot.send_message(user[0], text.format(user[2]))
        except KeyError:
            bot.send_message(user[0], FAIL_MESSAGE)

    connect.close()


def send_daily_results(bot, manager):
    """Sends daily results"""

    connect, cursor = db.connect_database(env)
    cursor.execute("SELECT user_id FROM employees")
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]

        if user_id in EMPLOYEES['рассылка'].values():
            kpi_daily = spredsheet.get_daily_statistic(
                manager, SHEET_KEY, WORKSHEET_ID)

            leaders = spredsheet.get_leaders_from_google_sheet(
                manager, SHEET_KEY, WORKSHEET_ID)

            statistic = ['Сводка за день\n']
            for key, value in kpi_daily.items():
                statistic.append(f'{key}: {value}')
            bot.send_message(user_id, '\n'.join(statistic))

        if leaders:
            bot.send_message(user_id, 'Красавчики дня:\n' + ', '.join(leaders))
        else:
            bot.send_message(user_id, 'Красавчиков дня нет')

    connect.close()


def send_weekly_results(bot, manager):
    """Sends weekly results"""

    connect, cursor = db.connect_database(env)
    cursor.execute("SELECT user_id FROM employees")
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]

        if user_id in EMPLOYEES['рассылка'].values():
            kpi_weekly = spredsheet.get_weekly_statistic(
                manager, SHEET_KEY, WORKSHEET_ID)

            statistic = ['Сводка за неделю\n']
            for key, value in kpi_weekly.items():
                statistic.append(f'{key}: {value}')

            bot.send_message(user_id, '\n'.join(statistic))

    connect.close()


def remind_to_send_lawsuits(bot):
    """Notifications abount sending lawsuits"""

    ids = map(str, EMPLOYEES['иски'].values())

    connect, cursor = db.connect_database(env)
    cursor.execute(
        "SELECT user_id, firstname FROM employees "
        f"WHERE user_id IN ({', '.join(ids)})"
    )
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]
        name = user[1]
        bot.send_message(user_id, LAWSUITS_MESSAGE.format(name))


def main():
    """Notification manager"""

    bot = telebot.TeleBot(TOKEN)
    manager = pygsheets.authorize(client_secret=CLIENT_SECRET_FILE)

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
