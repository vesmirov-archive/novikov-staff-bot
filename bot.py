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

# positions
POSITIONS = {
    'руководство': None,
    'помощь': None,
    'продажи': None,
    'делопроизводство': {
        'message': (
            'Пожалуйста, отправьте мне несколько ваших цифр '
            'в следующем формате:\n\n'
            '<заседаний>\n'
            '<решений>\n'
            '<подготовленных_исков>\n'
            '<иных_документов>\n'
            '<денег_получено>\n'
            '<событий_съедающих_бонус>\n\n'
            'Пример: 3 2 0 1 55000 0'
        ),
        'values_amount': 6,
    },
    'исполнение': {
        'message': (
            'Пожалуйста, отправьте мне несколько ваших цифр '
            'в следующем формате:\n\n'
            'Отправьте количественные данные в следующем формате:\n\n'
            '<заседаний>\n'
            '<решений>\n'
            '<получено_листов>\n'
            '<подано_листов>\n'
            '<напр_заявл_по_суд_расходам>\n'
            '<иных_документов>\n'
            '<денег_получено>\n\n'
            'Пример: 5 2 2 2 1 55000 0'
        ),
        'values_amount': 7,
    }
}

# messages
START_MESSAGE = (
    'Привет {}! Я бот юридического центра Новиков.\n'
    'Я собираю статистику сотрудников, просчитываю их KPI и '
    'фиксирую данные в Google Sheets.\n'
    'По любым вопросам можно обратиться к '
    '@vilagov или @karlos979.'
)
DENY_ANONIMUS_MESSAGE = (
    'У вас нет прав для использования данного бота.\n'
    'Обратитесь к @vilagov или @karlos979, если уверены '
    'что вам нужен доступ.'
)
DENY_STAFF_MESSAGE = 'У вас недостаточно прав для выполнение данной команды.'
ADDING_USER_MESSAGE = (
    'Отправьте данные добавляемого сотрудника в следующем формате:\n'
    '<telegram_ID_пользователя> <никнейм> <имя> '
    '<фамилия> <функционал> <админ_доступ_(да/нет)>\n\n'
    'При указании функционала сотрудника выберите одно из значений:\n'
    f'{", ".join(POSITIONS.keys())}\n\n'
    'Пример:\n'
    '123456789 ivanov Иван Иванов продажи нет'
)
DELETING_USER_MESSAGE = 'Отправьте мне id удаляемого сотрудника'
HELP_MESSAGE = (
    'Команды:\n'
    '/users - отобразить список пользователей (admin)\n'
    '/adduser - добавить пользователя (admin)\n'
    '/deluser - удалить пользователя (admin)\n'
    '/kpi - обновить свои показатели KPI за сегодняшний день\n'
    '/day - показать KPI отдела делопроизводства за сегодняшний день'
)


def permission_check(func):
    """
    User permission check decorator.
    If user id not in database, send 'deny access' message.
    """

    def inner(message):
        if db.user_has_permissions(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, DENY_ANONIMUS_MESSAGE)
    return inner


def is_admin_check(func):
    def inner(message):
        if db.user_is_admin_check(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, DENY_STAFF_MESSAGE)
    return inner


bot = telebot.TeleBot(TOKEN)
manager = pygsheets.authorize(service_file=SERVICE_FILE)
connect, cursor = db.connect_database(env)


markup = telebot.types.ReplyKeyboardMarkup(row_width=3)
kpi_btn = telebot.types.InlineKeyboardButton('/kpi')
today_btn = telebot.types.InlineKeyboardButton('/day')
week_check = telebot.types.InlineKeyboardButton('/lawsuits')
markup.add(kpi_btn, today_btn, week_check)


@bot.message_handler(commands=['start'])
@permission_check
def send_welcome(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    bot.send_message(user_id, START_MESSAGE.format(name), reply_markup=markup)


@bot.message_handler(commands=['help'])
@permission_check
def send_help_text(message):
    bot.send_message(message.from_user.id, HELP_MESSAGE)


@bot.message_handler(commands=['users'])
@permission_check
@is_admin_check
def send_list_users(message):
    users = db.list_users(cursor)
    bot.send_message(message.from_user.id, users)


@bot.message_handler(commands=['adduser'])
@permission_check
@is_admin_check
def start_adding_user(message):
    message = bot.send_message(message.from_user.id, ADDING_USER_MESSAGE)
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
        else:
            status = db.add_user(cursor, connect, user_id, username,
                                 firstname, lastname, position, is_admin)
            if status:
                bot.send_message(
                    message.from_user.id,
                    f'Пользователь "{username}" добавлен.'
                )
            else:
                bot.send_message(
                    message.from_user.id,
                    'Пользователь с таким ID уже имеется в базе.'
                )


@bot.message_handler(commands=['deluser'])
@permission_check
@is_admin_check
def start_deleting_user(message):
    message = bot.send_message(message.from_user.id, DELETING_USER_MESSAGE)
    bot.register_next_step_handler(message, deleting_user)


def deleting_user(message):
    user_id = message.text

    if not user_id.isnumeric():
        bot.send_message(
            message.from_user.id,
            'Неверный формат пользовательского ID.'
        )
    else:
        db.delete_user(cursor, connect, user_id)
        bot.send_message(
            message.from_user.id,
            f'Пользователь с ID "{user_id}" удален.'
        )


@bot.message_handler(commands=['kpi'])
@permission_check
def start_kpi_check(message):
    position = db.get_employee_position(cursor, message.from_user.id)

    if POSITIONS[position]:
        try:
            kwargs = {
                'position': position,
                'text': POSITIONS[position]['message'],
                'response_len': POSITIONS[position]['values_amount'],
            }
            message = bot.send_message(message.from_user.id, kwargs['text'])
            bot.register_next_step_handler(message, kpi_check, **kwargs)
        except (ValueError, KeyError):
            bot.send_message(
                message.from_user.id,
                'Что-то пошло не так. Свяжитесь с @vilagov.'
            )
    else:
        bot.send_message(
            message.from_user.id,
            'На данный период ваш KPI не отслеживается ботом.'
        )


def kpi_check(message, **kwargs):
    values = message.text.split()

    if len(values) < kwargs['response_len']:
        bot.send_message(message.from_user.id, 'Указаны не все показатели.')
    elif len(values) > kwargs['response_len']:
        bot.send_message(message.from_user.id, 'Указаны лишние показатели.')
    else:
        for i in values:
            if not i.isnumeric():
                bot.send_message(
                    message.from_user.id,
                    'Ответ должен быть количетсвенным и состоять из чисел.'
                )
                return
        status = spredsheet.write_KPI_to_google_sheet(
            manager,
            SHEET_KEY,
            WORKSHEET_ID,
            message.from_user.id,
            kwargs['position'],
            values
        )
        if status:
            bot.send_message(
                message.from_user.id,
                'Данные внесены. Хорошего вечера!'
            )
        else:
            bot.send_message(
                message.from_user.id,
                'Кажется вас не добавили в таблицу.\n'
                'Уведомите разработчиков.'
            )


@bot.message_handler(commands=['day'])
@permission_check
def day_statistic(message):
    kpi_daily = spredsheet.get_daily_statistic(
        manager, SHEET_KEY, WORKSHEET_ID)
    statistic = ['Статистика за день\n']
    for key, value in kpi_daily.items():
        statistic.append(f'{key}: {value}')
    bot.send_message(message.from_user.id, '\n'.join(statistic))


bot.polling()
connect.close()
