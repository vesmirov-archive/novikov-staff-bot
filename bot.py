"""
    Bot's module with specified commands
"""

import telebot
import pygsheets
from dotenv import dotenv_values

from service import db
from service import spredsheet

env = dotenv_values('.env')


# telegram
TOKEN = env.get('TELEGRAM_STAFF_TOKEN')
CHAT = env.get('TELEGRAM_CHAT_ID')

# google
SHEET_KEY = env.get('SHEET_KEY')
WORKSHEET_ID = env.get('WORKSHEET_STAFF_ID')
CLIENT_SECRET_FILE = env.get('CLIENT_SECRET_FILE')

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
            'Пример: 3 2 0 1 320000 0'
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
            'Пример: 5 2 2 2 1 320000 0'
        ),
        'values_amount': 7,
    }
}

# messages
START_MESSAGE = (
    u'Привет, {}! \U0001f60a Я бот юридического центра Новиков.\n'
    'Я собираю статистику сотрудников, просчитываю их KPI и '
    'фиксирую данные в Google Sheets.\n'
    'По любым вопросам можно обратиться к '
    '@vilagov или @karlos979.'
)
DENY_ANONIMUS_MESSAGE = (
    'У вас нет прав для пользования данным бота.\n'
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
)


def permission_check(func):
    """
    User permission check decorator.
    If user id not in database, send 'deny access' message
    """

    def inner(message):
        if db.user_has_permissions(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, DENY_ANONIMUS_MESSAGE)
    return inner


def user_is_admin_check(func):
    """Admin permission check decorator"""

    def inner(message):
        if db.user_is_admin_check(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, DENY_STAFF_MESSAGE)
    return inner


bot = telebot.TeleBot(TOKEN)
manager = pygsheets.authorize(client_secret=CLIENT_SECRET_FILE)
connect, cursor = db.connect_database(env)

markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
kpi_btn = telebot.types.InlineKeyboardButton('показатели \U0001f3af')
today_btn = telebot.types.InlineKeyboardButton('день \U0001f4c6')
week_btn = telebot.types.InlineKeyboardButton('неделя \U0001f5d3')
lawsuits = telebot.types.InlineKeyboardButton('иски \U0001f5ff')
leader = telebot.types.InlineKeyboardButton('красавчик \U0001f38a')
announce = telebot.types.InlineKeyboardButton('объявление \U0001f4ef')
markup.add(kpi_btn, leader, today_btn, week_btn, lawsuits, announce)


@bot.message_handler(commands=['start'])
@permission_check
def send_welcome(message):
    """Greet user"""

    user_id = message.from_user.id
    name = message.from_user.first_name
    bot.send_message(user_id, START_MESSAGE.format(name), reply_markup=markup)


@bot.message_handler(commands=['help'])
@permission_check
def send_help_text(message):
    """Send help-text to user"""

    bot.send_message(message.from_user.id, HELP_MESSAGE)


@bot.message_handler(commands=['users'])
@permission_check
@user_is_admin_check
def send_list_users(message):
    """Show all added users to this bot"""

    users = db.list_users(cursor)
    bot.send_message(message.from_user.id, users)


@bot.message_handler(commands=['adduser'])
@permission_check
@user_is_admin_check
def start_adding_user(message):
    """Add user to this bot"""

    message = bot.send_message(message.from_user.id, ADDING_USER_MESSAGE)
    bot.register_next_step_handler(message, adding_user)


def adding_user(message):
    """User adding process"""

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
@user_is_admin_check
def start_deleting_user(message):
    """Delete user"""

    message = bot.send_message(message.from_user.id, DELETING_USER_MESSAGE)
    bot.register_next_step_handler(message, deleting_user)


def deleting_user(message):
    """User deleting process"""

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


@bot.message_handler(regexp=r'показатели\S*')
@permission_check
def start_kpi_check(message):
    """Get today's values from user"""

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
            'На данный период ваш KPI '
            'не отслеживается ботом \U0001f44c\U0001f3fb'
        )


def kpi_check(message, **kwargs):
    """Values getting process"""

    values = message.text.split()

    if len(values) < kwargs['response_len']:
        bot.send_message(
            message.from_user.id,
            'Указаны не все показатели \u261d\U0001f3fb'
        )
    elif len(values) > kwargs['response_len']:
        bot.send_message(
            message.from_user.id,
            'Указаны лишние показатели \u261d\U0001f3fb'
        )
    else:
        for i in values:
            if not i.isnumeric():
                bot.send_message(
                    message.from_user.id,
                    'Ответ должен быть количетсвенным '
                    'и состоять из чисел \u261d\U0001f3fb'
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
                'Данные внесены \u2705\nХорошего вечера! \U0001f942'
            )
        else:
            bot.send_message(
                message.from_user.id,
                'Кажется вас не добавили в таблицу.\n'
                'Уведомите разработчиков.'
            )


@bot.message_handler(regexp=r'день\S*')
@permission_check
def day_statistic(message):
    """Send users values for today"""
    bot.send_message(
        message.from_user.id,
        'Минуту, собираю данные.\n'
        'Обычно это занимает не больше 20 секунд \U0001f552'
    )
    kpi_daily = spredsheet.get_daily_statistic_of_employee_in_division(
        manager, SHEET_KEY, WORKSHEET_ID)
    
    result = ['Статистика за день \U0001f4c6:\n']

    for name, values in kpi_daily.items():
        result.append(f'\U0001f464 {name}\n')
        for key, value in values.items():
            result.append(f'{key}: {value}')
        result.append('')

    bot.send_message(message.from_user.id, '\n'.join(result))


@bot.message_handler(regexp=r'неделя\S*')
@permission_check
def week_statistic(message):
    """Send users values for all week"""

    kpi_daily = spredsheet.get_weekly_statistic(
        manager, SHEET_KEY, WORKSHEET_ID)
    statistic = ['Статистика за неделю \U0001f5d3:\n']
    for key, value in kpi_daily.items():
        statistic.append(f'{key}: {value}')
    bot.send_message(message.from_user.id, '\n'.join(statistic))


@bot.message_handler(regexp=r'иски\S*')
@permission_check
@user_is_admin_check
def start_week_lawsuits(message):
    """Get specific value from user (lawsuits)"""

    bot.send_message(
        message.from_user.id,
        f'Привет {message.from_user.first_name}!\n'
        'Сколько было подано исков на этой неделе?'
    )
    bot.register_next_step_handler(message, week_lawsuits)


def week_lawsuits(message):
    """Value getting process (lawsuits)"""

    if message.text.isnumeric():
        status = spredsheet.write_lawsuits_to_google_sheet(
            manager, SHEET_KEY, WORKSHEET_ID, message.text)
        if status:
            bot.send_message(
                message.from_user.id,
                'Спасибо! Данные внесены \u2705'
            )
        else:
            bot.send_message(message.from_user.id, 'Что-то пошло не так.')
    else:
        bot.send_message(
            message.from_user.id,
            'Прости, я не понял. Попробуй снова и пришли пожалуйста данные '
            'в числовом формате \u261d\U0001f3fb'
        )


@bot.message_handler(regexp=r'красавчик\S*')
@permission_check
def show_the_leader(message):
    """Send the leader of the day"""

    leaders = spredsheet.get_leaders_from_google_sheet(
        manager, SHEET_KEY, WORKSHEET_ID)

    if leaders:
        bot.send_message(
            message.from_user.id,
            '\U0001f5ff Красавчики дня:\n' + ', '.join(leaders)
        )
    else:
        bot.send_message(message.from_user.id, 'Красавчиков дня нет')


@bot.message_handler(regexp=r'объявление\S*')
@permission_check
@user_is_admin_check
def start_make_announcement(message):
    """Make an announcement for all added users"""

    bot.send_message(
        message.from_user.id,
        f'Привет {message.from_user.first_name}! '
        'Пришли мне текст сообщения, а я отправлю '
        'его всем сотрудникам \U0001f4dd'
    )
    bot.register_next_step_handler(message, make_announcement)


def make_announcement(message):
    """Get announcement"""

    ids = db.return_users_ids(cursor)
    kwargs = {'text': message.text, 'ids': ids}
    bot.send_message(message.from_user.id, 'Записал. Отправляем? (да/нет)')
    bot.register_next_step_handler(message, send_announcement, **kwargs)


def send_announcement(message, **kwargs):
    """Announcement sending confirmation"""

    if message.text == 'да':
        for user_id in kwargs['ids']:
            bot.send_message(user_id, kwargs['text'])
        bot.send_message(
            message.from_user.id,
            'Готово! Сотрудники уведомлены \u2705'
        )
    elif message.text == 'нет':
        bot.send_message(
            message.from_user.id,
            'Принял. Отменяю \U0001f44c\U0001f3fb'
        )
    else:
        bot.send_message(
            message.from_user.id,
            'Не понял ответа. Отмена \U0001f44c\U0001f3fb'
        )


try:
  bot.polling()
except Exception as e:
  print(e)

connect.close()
