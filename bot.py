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
WORKSHEET_LAW_ID = env.get('WORKSHEET_LAW_ID')
WORKSHEET_SALES_ID = env.get('WORKSHEET_SALES_ID')

CLIENT_SECRET_FILE = env.get('CLIENT_SECRET_FILE')

# config
POSITIONS = {
    'руководство': {
        'worksheet': None,
        'руководитель': {},
        'заместитель': {},
        'помощник': {},
    },
    'делопроизводство': {
        'worksheet': WORKSHEET_LAW_ID,
        'ведение': {
            'message': (
                'Пожалуйста, отправьте мне количественные '
                'данные в следующем формате:\n\n'
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
                'Пожалуйста, отправьте мне следующие количественные:\n\n'
                '<заседаний>\n'
                '<решений>\n'
                '<получено_листов>\n'
                '<подано_листов>\n'
                '<иных_документов>\n'
                '<денег_получено>\n\n'
                '<напр_заявл_по_суд_расходам>\n'
                'Пример: 5 2 2 2 1 320000 0'
            ),
            'values_amount': 7,
        },
    },
    'продажи': {
        'worksheet': WORKSHEET_SALES_ID,
        'лиды': {
            'message': (
                'Пожалуйста, отправьте мне следующие данные:\n\n'
                '<залив_заявок>\n'
                '<залив_напр_на_осмотр>\n'
                '<неустойка_заявок>\n'
                '<неустойка_получ_инн>\n'
                '<приемка_заявок>\n'
                '<приемка_напр_на_осмотр>\n'
                '<рег_учет_заявок>\n'
                '<рег_учет_назначено_встреч_в_офисе>\n\n'
                'Пример: 10 5 5 2 5 3 1 1'
            ),
            'values_amount': 8,
        },
        'хантинг': {}
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
    '<telegram_ID_пользователя>\n<никнейм>\n<имя>\n'
    '<фамилия>\n<отдел>\n<позиция>\n<админ_доступ_(да/нет)>\n\n'
    'При указании отдела и позиции выбирайте из следующих значений:\n\n'
    'руководство:\n    руководитель, заместитель, помощник\n\n'
    'делопроизводство:\n    ведение, исполнение\n\n'
    'продажи:\n    лиды, хантинг\n\n'
    'Пример:\n'
    '123456789 ivanov Иван Иванов продажи хантинг нет'
)
DELETING_USER_MESSAGE = 'Отправьте мне id удаляемого сотрудника'
HELP_MESSAGE = (
    'Команды:\n'
    '/users - отобразить список пользователей (admin)\n'
    '/adduser - добавить пользователя (admin)\n'
    '/deluser - удалить пользователя (admin)\n\n'
    'Таблица:\n'
    'https://docs.google.com/spreadsheets/d/{}/edit'
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
    """
        Admin permission check decorator
    """

    def inner(message):
        if db.user_is_admin_check(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, DENY_STAFF_MESSAGE)
    return inner


bot = telebot.TeleBot(TOKEN)
manager = pygsheets.authorize(service_account_file=CLIENT_SECRET_FILE)
connect, cursor = db.connect_database(env)

# main keyboard
menu_markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
kpi_btn = telebot.types.InlineKeyboardButton('показатели \U0001f3af')
today_btn = telebot.types.InlineKeyboardButton('день \U0001f4c6')
week_btn = telebot.types.InlineKeyboardButton('неделя \U0001f5d3')
lawsuits_btn = telebot.types.InlineKeyboardButton('иски \U0001f5ff')
leader_btn = telebot.types.InlineKeyboardButton('красавчик \U0001f38a')
announce_btn = telebot.types.InlineKeyboardButton('объявление \U0001f4ef')
menu_markup.add(
    kpi_btn,
    leader_btn,
    today_btn,
    week_btn,
    lawsuits_btn,
    announce_btn
)

# statistic day keyboard
stat_day_markup = telebot.types.InlineKeyboardMarkup()
sales_day_btn = telebot.types.InlineKeyboardButton(
    'продажи', callback_data='день продажи')
law_day_btn = telebot.types.InlineKeyboardButton(
    'делопроизводство', callback_data='день делопроизводство')
stat_day_markup.add(sales_day_btn, law_day_btn)

# statistic week keyboard
stat_week_markup = telebot.types.InlineKeyboardMarkup()
sales_week_btn = telebot.types.InlineKeyboardButton(
    'продажи', callback_data='неделя продажи')
law_week_btn = telebot.types.InlineKeyboardButton(
    'делопроизводство', callback_data='неделя делопроизводство')
stat_week_markup.add(sales_week_btn, law_week_btn)

# statistic leader keyboard
leader_markup = telebot.types.InlineKeyboardMarkup()
law_leader_btn = telebot.types.InlineKeyboardButton(
    'делопроизводство', callback_data='красавчик делопроизводство')
leader_markup.add(law_leader_btn)


@bot.message_handler(commands=['start'])
@permission_check
def send_welcome(message):
    """
        Greet user
    """

    user_id = message.from_user.id
    name = message.from_user.first_name
    bot.send_message(
        user_id, START_MESSAGE.format(name), reply_markup=menu_markup)


@bot.message_handler(commands=['help'])
@permission_check
def send_help_text(message):
    """
        Send help-text to user
    """

    bot.send_message(message.from_user.id, HELP_MESSAGE.format(SHEET_KEY))


@bot.message_handler(commands=['users'])
@permission_check
@user_is_admin_check
def send_list_users(message):
    """
        Show all added users to this bot
    """

    users = db.list_users(cursor)
    bot.send_message(message.from_user.id, users)


@bot.message_handler(commands=['adduser'])
@permission_check
@user_is_admin_check
def start_adding_user(message):
    """
        Add user to this bot
    """

    message = bot.send_message(message.from_user.id, ADDING_USER_MESSAGE)
    bot.register_next_step_handler(message, adding_user)


def adding_user(message):
    """
        User adding process
    """

    data = message.text.split()

    if len(data) != 7:
        bot.send_message(message.from_user.id, 'Неверный формат.')
        return
    if data[4] not in POSITIONS.keys():
        bot.send_message(
            message.from_user.id,
            'Указанный отдел не представлен в списке.'
        )
        return
    if data[5] not in POSITIONS[data[4]].keys():
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
            department = data[4]
            position = data[5]
            is_admin = True if data[6] == 'да' else False

        except (ValueError, KeyError) as e:
            bot.send_message(
                message.from_user.id, 'Неверный формат.')
        else:
            status = db.add_user(cursor, connect, user_id, username,
                                 firstname, lastname, department,
                                 position, is_admin)
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
    """
        Delete user
    """

    message = bot.send_message(message.from_user.id, DELETING_USER_MESSAGE)
    bot.register_next_step_handler(message, deleting_user)


def deleting_user(message):
    """
        User deleting process
    """

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
    """
        Get today's values from user
    """

    kwargs = db.get_employee_department_and_position(
        cursor, message.from_user.id)
    department = kwargs['department']
    position = kwargs['position']
    try:
        if POSITIONS[department][position]:
            kwargs.update(
                response_len=POSITIONS[department][position]['values_amount'])
            message = bot.send_message(
                message.from_user.id,
                POSITIONS[department][position]['message']
            )
            bot.register_next_step_handler(message, kpi_check, **kwargs)
        else:
            bot.send_message(
                message.from_user.id,
                'На данный период ваш KPI '
                'не отслеживается ботом \U0001f44c\U0001f3fb'
            )
    except (ValueError, KeyError):
        bot.send_message(
            message.from_user.id,
            'Что-то пошло не так. Свяжитесь с администратором.'
        )


def kpi_check(message, **kwargs):
    """
        Values getting process
    """

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
        department = kwargs['department']

        status = spredsheet.write_KPI_to_google_sheet(
            manager,
            SHEET_KEY,
            POSITIONS[department]['worksheet'],
            message.from_user.id,
            department,
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
def day_statistic_start_message(message):
    """
        Ask of which division statistic is needed
    """

    bot.send_message(
        message.chat.id,
        text='Выберите отдел',
        reply_markup=stat_day_markup
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith('день'))
def day_statistic(call):
    """
        Send users values for today
    """

    bot.answer_callback_query(
        callback_query_id=call.id,
        text=(
            'Минуту, собираю данные.\n'
            'Обычно это занимает не больше 20 секунд \U0001f552'
        )
    )
    
    department = call.data.split()[-1]

    kpi_daily = spredsheet.get_daily_statistic(
        manager,
        SHEET_KEY,
        POSITIONS[department]['worksheet'],
        department
    )

    result = []
    bot.send_message(call.message.chat.id, 'Статистика за день \U0001f4c6')
    result.extend([f'{k}: {v}' for k, v in kpi_daily.items()])
    bot.send_message(call.message.chat.id, '\n'.join(result))

    result = []
    bot.send_message(
        call.message.chat.id, 'Статистика по сотрудникам \U0001F465')
    kpi_daily_detail = spredsheet.get_daily_detail_statistic(
        manager,
        SHEET_KEY,
        POSITIONS[department]['worksheet'],
        department
    )
    for position, employees in kpi_daily_detail.items():
        employees_result = []
        if employees:
            for employee, values in employees.items():
                employees_result.append(f'\n\U0001F464 {employee}:\n')
                employees_result.append('\n'.join([f'{k}: {v}' for k, v in values.items()]))
            result.append(f'\n\n\U0001F53D {position.upper()}')
            result.append('\n'.join(employees_result))
    bot.send_message(call.message.chat.id, '\n'.join(result))


@bot.message_handler(regexp=r'неделя\S*')
@permission_check
def week_statistic_start_message(message):
    """
        Ask of which division statistic is needed
    """

    bot.send_message(
        message.chat.id,
        text='Выберите отдел',
        reply_markup=stat_week_markup
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith('неделя'))
def week_statistic(call):
    """
        Send users values for all week
    """
    bot.answer_callback_query(
        callback_query_id=call.id,
        text=(
            'Собираю данные.\n'
            'Обычно это занимает не больше 5 секунд \U0001f552'
        )
    )
    
    department = call.data.split()[-1]

    kpi_daily = spredsheet.get_weekly_statistic(
        manager,
        SHEET_KEY,
        POSITIONS[department]['worksheet'],
        department
    )

    result = []
    bot.send_message(call.message.chat.id, 'Статистика за неделю \U0001f5d3')
    result.extend([f'{k}: {v}' for k, v in kpi_daily.items()])
    bot.send_message(call.message.chat.id, '\n'.join(result))


@bot.message_handler(regexp=r'иски\S*')
@permission_check
@user_is_admin_check
def start_week_lawsuits(message):
    """
        Get specific value from user (lawsuits)
    """

    bot.send_message(
        message.from_user.id,
        f'Привет {message.from_user.first_name}!\n'
        'Сколько было подано исков на этой неделе?'
    )
    bot.register_next_step_handler(message, week_lawsuits)


def week_lawsuits(message):
    """
        Value getting process (lawsuits)
    """

    if message.text.isnumeric():
        status = spredsheet.write_lawsuits_to_google_sheet(
            manager, SHEET_KEY, WORKSHEET_LAW_ID, message.text)
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
def show_the_leader_start_message(message):
    """
        Ask of which division statistic is needed
    """

    bot.send_message(
        message.chat.id,
        text='Выберите отдел',
        reply_markup=leader_markup
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith('красавчик'))
def show_the_leader(call):
    """
        Send the leader of the day
    """

    department = call.data.split()[-1]

    leaders = spredsheet.get_leaders_from_google_sheet(
        manager,
        SHEET_KEY,
        POSITIONS[department]['worksheet'],
        department
    )

    if leaders:
        bot.send_message(
            call.message.chat.id,
            '\U0001f5ff Красавчики дня:\n' + ', '.join(leaders)
        )
    else:
        bot.send_message(call.message.chat.id, 'Красавчиков дня нет')


@bot.message_handler(regexp=r'объявление\S*')
@permission_check
@user_is_admin_check
def start_make_announcement(message):
    """
        Make an announcement for all added users
    """

    bot.send_message(
        message.from_user.id,
        f'Привет {message.from_user.first_name}! '
        'Пришли мне текст сообщения, а я отправлю '
        'его всем сотрудникам \U0001f4dd'
    )
    bot.register_next_step_handler(message, make_announcement)


def make_announcement(message):
    """
        Get announcement
    """

    ids = db.return_users_ids(cursor)
    kwargs = {'text': message.text, 'ids': ids}
    bot.send_message(message.from_user.id, 'Записал. Отправляем? (да/нет)')
    bot.register_next_step_handler(message, send_announcement, **kwargs)


def send_announcement(message, **kwargs):
    """
        Announcement sending confirmation
    """

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


bot.polling()

connect.close()
