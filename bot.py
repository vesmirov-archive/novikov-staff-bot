import datetime
import json

import telebot
import pygsheets
from dotenv import dotenv_values

from service import db

env = dotenv_values('.env')


# telegram
TOKEN = env.get('TELEGRAM_TOKEN')
CHAT = env.get('TELEGRAM_CHAT_ID')

# google
SHEET_KEY = env.get('SHEET_KEY')
WORKSHEET_ID = env.get('WORKSHEET_ID')
SERVICE_FILE = env.get('SERVICE_FILE')

# messages
START = (
    'Привет {}! Я бот юридического центра Новиков.\n'
    'Я собираю статистику сотрудников, просчитываю их KPI и '
    'фиксирую данные в Google Sheets.\n'
    'По любым вопросам можно обратиться к '
    '@vilagov или @karlos979.'
)
DENY_ANONIMUS = (
    'У вас нет прав для использования данного бота.\n'
    'Обратитесь к @vilagov или @karlos979, если уверены '
    'что вам нужен доступ.'
)
DENY_REGISTERED = 'У вас недостаточно прав для выполнение данной команды.'
HELP = (
    'Команды:\n'
    '/users - отобразить список пользователей\n'
    '/adduser - добавить пользователя'
)
POSITIONS = [
    'руководство',
    'помощь',
    'продажи',
    'делопроизводство',
    'исполнительное делопроизводство',
]


def permission_check(func):
    """
    User permission check decorator.
    If user id not in database, send 'deny access' message.
    """

    def inner(message):
        if db.user_has_permissions(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, START_ANONIMUS)
    return inner


def is_admin_check(func):
    def inner(message):
        if db.user_is_admin_check(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, DENY_REGISTERED)
    return inner


bot = telebot.TeleBot(TOKEN)
manager = pygsheets.authorize(service_file=SERVICE_FILE)
connect, cursor = db.connect_database(env)


markup = telebot.types.ReplyKeyboardMarkup(row_width=3)
users_btn = telebot.types.KeyboardButton('/users')
help_btn = telebot.types.InlineKeyboardButton('/help')
markup.add(users_btn, help_btn)


@bot.message_handler(commands=['start'])
@permission_check
def send_welcome(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    bot.send_message(user_id, START.format(name))


@bot.message_handler(commands=['help'])
@permission_check
def send_help_text(message):
    bot.send_message(message.from_user.id, HELP)


@bot.message_handler(commands=['users'])
@permission_check
def send_list_users(message):
    users = db.list_users(cursor)
    bot.send_message(message.from_user.id, users)


@bot.message_handler(commands=['adduser'])
@permission_check
@is_admin_check
def start_adding_user(message):
    message = bot.send_message(
        message.from_user.id,
        'Отправьте данные добавляемого сотрудника в следующем формате:\n'
        '<ID_пользователя> <никнейм> <имя> '
        '<фамилия> <функционал> <админ_доступ_(да/нет)>\n\n'
        'При указании функционала сотрудника выберите одно из значений:\n'
        'руководство, помощь, продажи, делопроизводство, '
        'исполнительное делопроизводство\n\n'
        'Пример:\n'
        '123456789 ivanov Иван Иванов продажи нет'
    )
    bot.register_next_step_handler(message, adding_user)


def adding_user(message):
    data = message.text.split()

    if len(data) != 6:
        bot.send_message(message.from_user.id, 'Неверный формат.')
    elif data[4] not in POSITIONS:
        bot.send_message(
            message.from_user.id,
            'Указанный функционал отсутствует в списке.'
        )
    else:
        try:
            user_id = int(data[0])
            username = data[1]
            firstname = data[2]
            lastname = data[3]
            position = data[4]
            is_admin = True if data[5] == 'да' else False
        except ValueError:
            bot.send_message(
                message.from_user.id, 'Неверный формат.')
        finally:
            db.add_user(cursor, connect, user_id, username,
                        firstname, lastname, position, is_admin)
            bot.send_message(
                message.from_user.id,
                f'Пользователь "{username}" добавлен.'
            )


@bot.message_handler(commands=['kpi'])
@permission_check
def start_kpi_check(message):
    message = bot.send_message(
        message.from_user.id,
        'Как прошел сегодняшний рабочий день?\n\n'
        'Отправьте данные в следующем формате:\n'
        '<заседаний> <решений> <написано_исков> '
        '<подано_исков> <количество_штрафов>\n'
        'Пример: 3 2 0 1 0'
    )
    bot.register_next_step_handler(message, kpi_check)


def kpi_check(message):
    values = message.text.split()

    if len(values) < 5:
        bot.send_message(message.from_user.id, 'Указаны не все показатели.')
    elif len(values) > 5:
        bot.send_message(message.from_user.id, 'Указаны лишние показатели.')
    else:
        for i in values:
            if not i.isnumeric():
                bot.send_message(
                    message.from_user.id, 'Неверный формат.')
                return
        position = get_employee_position(cursor, message.from_user.id)
        data = {
            'user_id': message.from_user.id,
            'position': position,
            'values': values
        }
        write_KPI_to_google_sheet(manager, SHEET_KEY, WORKSHEET_ID, data)


bot.polling()
connect.close()
