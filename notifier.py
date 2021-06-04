import telebot
import pygsheets
from dotenv import dotenv_values

from service import db
from service import spredsheet

env = dotenv_values('.env')

# telegram
TOKEN = env.get('TELEGRAM_TOKEN')
CHAT = env.get('TELEGRAM_CHAT_ID')

# google
SHEET_KEY = env.get('SHEET_KEY')
WORKSHEET_ID = env.get('WORKSHEET_ID')
SERVICE_FILE = env.get('SERVICE_FILE')

# messages
KPI_MESSAGE = (
    'Привет {}! Рабочий день закончен, самое время заняться своими делами :)'
    'Но, кажется вы забыли прислать мне ваш KPI.\n'
    'Пожалуйста, пришлите мне ваши цифры за сегодня, нажав: /kpi.'
)

# employees with next positions will be notified
TRACKED_POSOTIONS = [
    'делопроизводство',
    'исполнение'
]


def main():
    connect, cursor = db.connect_database(env)
    bot = telebot.TeleBot(TOKEN)
    manager = pygsheets.authorize(service_file=SERVICE_FILE)

    cursor.execute("SELECT user_id, position, firstname FROM employees")
    users = cursor.fetchall()

    for user in users:
        if user[1] not in TRACKED_POSOTIONS:
            continue

        try:
            filled = spredsheet.check_if_already_filled(
                manager, SHEET_KEY, WORKSHEET_ID, user[0], user[1])

            if not filled:
                bot.send_message(
                    user[0],
                    f'{user[2]}, как прошел твой день?\n'
                    'Нажми /kpi, чтобы отправить мне свои результаты :)'
                )

        except KeyError:
            bot.send_message(
                user[0],
                'Я попытался с вами связаться, '
                'но кажется вас не добавили в мой список :(\n'
                'Пожалуйста, сообщите об ошибке ответственному лицу.'
            )

    connect.close()


if __name__ == '__main__':
    main()
