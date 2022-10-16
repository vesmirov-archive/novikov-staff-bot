"""
    Bot's module with specified commands
"""
import json

from dotenv import dotenv_values
import pygsheets
import telebot

from messages import (
    DENY_MESSAGE,
    DENY_ANONIMUS_MESSAGE,
    HELP_MESSAGE,
    MESSAGES_CONFIG,
    PLAN_MESSAGE,
    START_MESSAGE,
    USER_ADD_MESSAGE,
    USER_DELETE_MESSAGE,
)
from service import db
from service import spredsheet

env = dotenv_values('.env')

TOKEN = env.get('TELEGRAM_STAFF_TOKEN')
CHAT = env.get('TELEGRAM_CHAT_ID')

CLIENT_SECRET_FILE = env.get('CLIENT_SECRET_FILE')

with open('config.json', 'r') as file:
    CONFIG = json.loads(file.read())


def permission_check(func):
    """
        User permission check decorator.
        If user's id not in database, send 'deny access' message
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
            bot.send_message(message.from_user.id, DENY_MESSAGE)
    return inner


bot = telebot.TeleBot(TOKEN)
manager = pygsheets.authorize(service_account_file=CLIENT_SECRET_FILE)
connect, cursor = db.connect_database(env)

# main keyboard
menu_markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
kpi_btn = telebot.types.InlineKeyboardButton('мои показатели \U0001f3af')
plan = telebot.types.InlineKeyboardButton('мой план \U0001f4b5')
today_btn = telebot.types.InlineKeyboardButton('день \U0001f4c6')
week_btn = telebot.types.InlineKeyboardButton('неделя \U0001f5d3')
lawsuits_btn = telebot.types.InlineKeyboardButton('иски \U0001f5ff')
income_btn = telebot.types.InlineKeyboardButton('выручка \U0001f4b0')
leader_btn = telebot.types.InlineKeyboardButton('красавчики \U0001F3C6')
announce_btn = telebot.types.InlineKeyboardButton('объявление \U0001f4ef')
menu_markup.add(
    kpi_btn,
    plan,
    today_btn,
    week_btn,
    lawsuits_btn,
    income_btn,
    leader_btn,
    announce_btn
)

# statistic day keyboard
stat_day_markup = telebot.types.InlineKeyboardMarkup()
sales_day_btn = telebot.types.InlineKeyboardButton(
    'продажи', callback_data='день продажи')
law_day_btn = telebot.types.InlineKeyboardButton(
    'делопроизводство', callback_data='день делопроизводство')
head_day_markup = telebot.types.InlineKeyboardButton(
    'руководство', callback_data='день руководство')
stat_day_markup.add(sales_day_btn, law_day_btn, head_day_markup)

# statistic week keyboard
stat_week_markup = telebot.types.InlineKeyboardMarkup()
sales_week_btn = telebot.types.InlineKeyboardButton(
    'продажи', callback_data='неделя продажи')
law_week_btn = telebot.types.InlineKeyboardButton(
    'делопроизводство', callback_data='неделя делопроизводство')
head_week_markup = telebot.types.InlineKeyboardButton(
    'руководство', callback_data='неделя руководство')
stat_week_markup.add(sales_week_btn, law_week_btn, head_week_markup)

# leader keyboard
leader_markup = telebot.types.InlineKeyboardMarkup()
law_leader_btn = telebot.types.InlineKeyboardButton(
    'делопроизводство', callback_data='красавчик делопроизводство')
leader_markup.add(law_leader_btn)

# plan keyboard
plan_makup = telebot.types.InlineKeyboardMarkup()
plan_day_btn = telebot.types.InlineKeyboardButton(
    'на день', callback_data='план день')
plan_week_btn = telebot.types.InlineKeyboardButton(
    'на неделю', callback_data='план неделя')
plan_makup.add(plan_day_btn, plan_week_btn)


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

    bot.send_message(
        message.from_user.id,
        HELP_MESSAGE.format(
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['план']['table']
        )
    )


@bot.message_handler(commands=['users'])
@permission_check
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

    message = bot.send_message(message.from_user.id, USER_ADD_MESSAGE)
    bot.register_next_step_handler(message, adding_user)


def adding_user(message):
    """
        User adding process
    """

    data = message.text.split()

    if len(data) != 7:
        bot.send_message(message.from_user.id, 'Неверный формат.')
        return
    if data[4] not in MESSAGES_CONFIG.keys():
        bot.send_message(
            message.from_user.id,
            'Указанный отдел не представлен в списке.'
        )
        return
    if data[5] not in MESSAGES_CONFIG[data[4]].keys():
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

        except (ValueError, KeyError):
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

    message = bot.send_message(message.from_user.id, USER_DELETE_MESSAGE)
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


@bot.message_handler(regexp=r'мой план\S*')
def start_set_plan(message):
    """
        Start setting personal plan
    """
    bot.send_message(
        message.from_user.id,
        'На какой срок нужно выставить план?',
        reply_markup=plan_makup
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith('план'))
def prepate_set_plan(call):
    kwargs = db.get_employee_department_and_position(
        cursor, call.from_user.id)
    department = kwargs['department']
    position = kwargs['position']
    kwargs['period'] = call.data.split()[-1]

    try:
        employee = CONFIG['подразделения'][department][position]['сотрудники'][str(call.from_user.id)]  # noqa
    except KeyError:
        bot.send_message(
            call.from_user.id,
            'Кажется я вас не узнаю. Свяжитесь с администратором.'
        )
    else:
        if employee['планирование']:
            if employee['планирование'][kwargs['period']]:
                bot.send_message(call.from_user.id, PLAN_MESSAGE)
                kwargs['valamount'] = len(employee['планирование'][kwargs['period']]['текущая']['план'].keys())  # noqa
                message = bot.send_message(
                    call.from_user.id,
                    '\n'.join(employee['планирование'][kwargs['period']]['текущая']['план'].keys())  # noqa
                )
                bot.register_next_step_handler(message, set_plan, **kwargs)
            else:
                bot.send_message(
                    call.from_user.id,
                    'Бот не отслеживает ваши планы на '
                    'указанный срок \U0001f44c\U0001f3fb'
                )
        else:
            bot.send_message(
                call.from_user.id,
                'Ваши планы не отслеживаются ботом \U0001f44c\U0001f3fb'
            )


def set_plan(message, **kwargs):
    """
        Setting personal plan
    """

    values = message.text.split()

    if len(values) < kwargs['valamount']:
        bot.send_message(
            message.from_user.id,
            'Указаны не все показатели \u261d\U0001f3fb'
        )
        return
    elif len(values) > kwargs['valamount']:
        bot.send_message(
            message.from_user.id,
            'Указаны лишние показатели \u261d\U0001f3fb'
        )
        return
    else:
        for i in values:
            if not i.isnumeric():
                bot.send_message(
                    message.from_user.id,
                    'Ответ должен быть количетсвенным '
                    'и состоять из чисел \u261d\U0001f3fb'
                )
                return

    status = spredsheet.write_plan_to_google_sheet(
        manager,
        CONFIG['google']['tables']['план']['table'],
        CONFIG['google']['tables']['план']['sheets'][kwargs['department']],
        message.from_user.id,
        kwargs['department'],
        kwargs['position'],
        kwargs['period'],
        values
    )
    if status:
        table_url = 'https://docs.google.com/spreadsheets/d/{}/edit#gid={}/'.format(
            CONFIG['google']['tables']['план']['table'],
            CONFIG['google']['tables']['план']['sheets'][kwargs['department']]
        )
        bot.send_message(
            message.from_user.id,
            'Цель установлена \u2705\n\n'
            'Можешь отслеживать свои показатели в таблице:\n'
            f'{table_url}\n\n'
            'Продуктивной недели!'
        )
    else:
        bot.send_message(
            message.from_user.id,
            'Кажется вас не добавили в таблицу.\n'
            'Уведомите разработчиков.'
        )


@bot.message_handler(regexp=r'мои показатели\S*')
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
        if MESSAGES_CONFIG[department][position]:
            kwargs.update(response_len=MESSAGES_CONFIG[department][position]['values_amount'])  # noqa
            message = bot.send_message(
                message.from_user.id,
                MESSAGES_CONFIG[department][position]['message']
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
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets'][department],
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
            'Обычно это занимает не больше 5 секунд \U0001f552'
        )
    )

    department = call.data.split()[-1]

    kpi_daily = spredsheet.get_daily_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
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
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department
    )

    result = []
    bot.send_message(call.message.chat.id, 'Статистика за неделю \U0001f5d3')
    result.extend([f'{k}: {v}' for k, v in kpi_daily.items()])
    bot.send_message(call.message.chat.id, '\n'.join(result))


@bot.message_handler(regexp=r'выручка\S*')
@permission_check
@user_is_admin_check
def start_day_income(message):
    """
        Get specific value from user (income)
    """

    bot.send_message(
        message.from_user.id,
        f'Привет {message.from_user.first_name}!\n'
        'Какая сумма выручки на сегодня?'
    )
    bot.register_next_step_handler(message, day_income)

def day_income(message):
    """
        Value getting process (income)
    """

    if message.text.isnumeric():
        status = spredsheet.write_income_to_google_sheet(
            manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets']['руководство'],
            message.text
        )
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
            manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets']['делопроизводство'],
            message.text
        )
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
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department
    )

    if leaders:
        bot.send_message(
            call.message.chat.id,
            '\U0001f38a Красавчики дня: ' + ', '.join(leaders)
        )
    else:
        bot.send_message(
            call.message.chat.id,
            '\U0001f5ff Красавчиков дня нет'
        )


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

    if message.text.lower() == 'да':
        for user_id in kwargs['ids']:
            bot.send_message(user_id, kwargs['text'])
        bot.send_message(
            message.from_user.id,
            'Готово! Сотрудники уведомлены \u2705'
        )
    elif message.text.lower() == 'нет':
        bot.send_message(
            message.from_user.id,
            'Принял. Отменяю \U0001f44c\U0001f3fb'
        )
    else:
        bot.send_message(
            message.from_user.id,
            'Не понял ответа. Отмена \U0001f44c\U0001f3fb'
        )


if __name__ == '__main__':
    while True:
        try:
            bot.polling()
        except Exception as e:
            time.sleep(5)
            print(e)

connect.close()
