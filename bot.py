import json
import pygsheets
import telebot
import time
from dotenv import dotenv_values

import messages
from service import db
from service import spredsheet

env = dotenv_values('.env')

TOKEN = env.get('TELEGRAM_STAFF_TOKEN')
CHAT = env.get('TELEGRAM_CHAT_ID')
CLIENT_SECRET_FILE = env.get('CLIENT_SECRET_FILE')

# TODO: stop using json config (#6)
with open('config.json', 'r') as file:
    CONFIG = json.loads(file.read())

bot = telebot.TeleBot(TOKEN)
manager = pygsheets.authorize(service_account_file=CLIENT_SECRET_FILE)
connect, cursor = db.connect_database(env)


# Markups

menu_markup = telebot.types.ReplyKeyboardMarkup(row_width=3)
menu_markup.add(
    telebot.types.InlineKeyboardButton('мои показатели \U0001f3af'),
    telebot.types.InlineKeyboardButton('мой план \U0001f4b5'),
    telebot.types.InlineKeyboardButton('день \U0001f4c6'),
    telebot.types.InlineKeyboardButton('неделя \U0001f5d3'),
    telebot.types.InlineKeyboardButton('иски \U0001f5ff'),
    telebot.types.InlineKeyboardButton('выручка \U0001f4b0'),
    telebot.types.InlineKeyboardButton('красавчики \U0001F3C6'),
    telebot.types.InlineKeyboardButton('объявление \U0001f4ef'),
)

statistic_day_markup = telebot.types.InlineKeyboardMarkup()
statistic_day_markup.add(
    telebot.types.InlineKeyboardButton('продажи', callback_data='день продажи'),
    telebot.types.InlineKeyboardButton('делопроизводство', callback_data='день делопроизводство'),
    telebot.types.InlineKeyboardButton('руководство', callback_data='день руководство'),
)

stat_week_markup = telebot.types.InlineKeyboardMarkup()
stat_week_markup.add(
    telebot.types.InlineKeyboardButton('продажи', callback_data='неделя продажи'),
    telebot.types.InlineKeyboardButton('делопроизводство', callback_data='неделя делопроизводство'),
    telebot.types.InlineKeyboardButton('руководство', callback_data='неделя руководство'),
)

leader_markup = telebot.types.InlineKeyboardMarkup()
leader_markup.add(
    telebot.types.InlineKeyboardButton('делопроизводство', callback_data='красавчик делопроизводство'),
)

plan_makup = telebot.types.InlineKeyboardMarkup()
plan_makup.add(
    telebot.types.InlineKeyboardButton('на день', callback_data='план день'),
    telebot.types.InlineKeyboardButton('на неделю', callback_data='план неделя'),
)


# Permissions

def user_has_permission(func):
    """
    Permission decorator.
    Checks if the telegram user is in DB and has access to the bot.
    Otherwise, sends an error message.
    """

    def inner(message):
        if db.user_exists(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, messages.DENY_ANONIMUS_MESSAGE)
    return inner


def user_is_admin(func):
    """
    Permission decorator.
    Checks if the telegram user is admin (DB: "is_admin" field).
    Otherwise, sends an error message.
    """

    def inner(message):
        if db.user_is_admin(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, messages.DENY_MESSAGE)
    return inner


# Bot commands actions

@bot.message_handler(commands=['start'])
@user_has_permission
def send_welcome(message):
    """TODO"""

    user_id = message.from_user.id
    name = message.from_user.first_name
    bot.send_message(user_id, messages.START_MESSAGE.format(name), reply_markup=menu_markup)


@bot.message_handler(commands=['help'])
@user_has_permission
def send_help_text(message):
    """TODO"""

    bot.send_message(
        message.from_user.id,
        messages.HELP_MESSAGE.format(
            # TODO: stop using json config (#6)
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['план']['table'],
        ),
    )


@bot.message_handler(commands=['users'])
@user_has_permission
def send_list_users(message):
    """TODO"""

    users = db.list_users(cursor)
    bot.send_message(message.from_user.id, users)


@bot.message_handler(commands=['adduser'])
@user_has_permission
@user_is_admin
def add_user_command_handler(message):
    """TODO"""

    def add_user(handler_message):
        data = handler_message.text.split()

        if len(data) != 7:
            bot.send_message(handler_message.from_user.id, 'Неверный формат.')
        elif data[4] not in messages.MESSAGES_CONFIG.keys():
            bot.send_message(handler_message.from_user.id, 'Указанный отдел не представлен в списке.')
        elif data[5] not in messages.MESSAGES_CONFIG[data[4]].keys():
            bot.send_message(handler_message.from_user.id, 'Указанный функционал отсутствует в списке.')
        else:
            try:
                user_id, username, firstname, lastname, department, position = data[0:6]
                is_admin = True if data[6] == 'да' else False
                args = cursor, connect, int(user_id), username, firstname, lastname, department, position, is_admin
            except (ValueError, KeyError):
                bot.send_message(handler_message.from_user.id, 'Неверный формат.')
            else:
                user_added = db.add_user(*args)
                if user_added:
                    bot.send_message(handler_message.from_user.id, 'Пользователь добавлен.')
                else:
                    bot.send_message(handler_message.from_user.id, f'Пользователь уже добавлен в базу (ID: {user_id}).')

    message = bot.send_message(message.from_user.id, messages.USER_ADD_MESSAGE)
    bot.register_next_step_handler(message, add_user)


@bot.message_handler(commands=['deluser'])
@user_has_permission
@user_is_admin
def delete_user_command_handler(message):
    """TODO"""

    def delete_user(handler_message):
        user_id = handler_message.text

        if user_id.isnumeric():
            db.delete_user(cursor, connect, user_id)
            bot.send_message(handler_message.from_user.id, f'Пользователь с ID "{user_id}" удален.')
        else:
            bot.send_message(handler_message.from_user.id, 'Неверный формат пользовательского ID.')

    message = bot.send_message(message.from_user.id, messages.USER_DELETE_MESSAGE)
    bot.register_next_step_handler(message, delete_user)


# Bot buttons actions

@bot.message_handler(regexp=r'мой план\S*')
def set_plan_message_handler(message):
    """TODO"""

    bot.send_message(message.from_user.id, 'На какой срок нужно выставить план?', reply_markup=plan_makup)


@bot.callback_query_handler(func=lambda c: c.data.startswith('план'))
def set_plan_callback(call):
    """TODO"""

    def set_plan(handler_message, **kwargs):
        values = handler_message.text.split()

        if len(values) < kwargs['valamount']:
            bot.send_message(handler_message.from_user.id, 'Указаны не все показатели \u261d\U0001f3fb')
        elif len(values) > kwargs['valamount']:
            bot.send_message(handler_message.from_user.id, 'Указаны лишние показатели \u261d\U0001f3fb')
        elif not all(value.isnumeric() for value in values):
            bot.send_message(handler_message.from_user.id,
                             'Ответ должен быть количетсвенным и состоять из чисел \u261d\U0001f3fb')
        else:
            # TODO: stop using json config (#6)
            # TODO: refactor spreadsheet module (#12)
            status = spredsheet.write_plan_to_google_sheet(
                manager,
                CONFIG['google']['tables']['план']['table'],
                CONFIG['google']['tables']['план']['sheets'][kwargs['department']],
                handler_message.from_user.id,
                kwargs['department'],
                kwargs['position'],
                kwargs['period'],
                values,
            )
            if status:
                table_url = 'https://docs.google.com/spreadsheets/d/{}/edit#gid={}/'.format(
                    CONFIG['google']['tables']['план']['table'],
                    CONFIG['google']['tables']['план']['sheets'][kwargs['department']],
                )
                bot.send_message(
                    handler_message.from_user.id,
                    f'Цель установлена \u2705\n\nМожно отследить свои показатели в таблице:\n{table_url}\n\n',
                )
            else:
                # TODO: logging (#10)
                bot.send_message(handler_message.from_user.id, 'Вас нет в таблице. Администратор оповещен.')

    kwargs = db.get_employee_department_and_position(cursor, call.from_user.id)
    department = kwargs['department']
    position = kwargs['position']

    kwargs['period'] = call.data.split()[-1]

    try:
        # TODO: stop using json config (#6)
        employee = CONFIG['подразделения'][department][position]['сотрудники'][str(call.from_user.id)]
    except KeyError:
        # TODO: logging (#10)
        bot.send_message(call.from_user.id, 'Я вас не узнаю. Администратор оповещен.')
    else:
        if employee['планирование']:
            if employee['планирование'][kwargs['period']]:
                bot.send_message(call.from_user.id, messages.PLAN_MESSAGE)
                kwargs['valamount'] = len(employee['планирование'][kwargs['period']]['текущая']['план'].keys())
                message = bot.send_message(
                    call.from_user.id,
                    '\n'.join(employee['планирование'][kwargs['period']]['текущая']['план'].keys()),
                )
                bot.register_next_step_handler(message, set_plan, **kwargs)
            else:
                bot.send_message(call.from_user.id, 'Ваши планы на указанный срок не отслеживаются \U0001f44c\U0001f3fb')
        else:
            bot.send_message(call.from_user.id, 'Ваши планы не отслеживаются ботом \U0001f44c\U0001f3fb')


@bot.message_handler(regexp=r'мои показатели\S*')
@user_has_permission
def kpi_check_message_handler(message):
    """TODO"""

    def kpi_check(handler_message, **kwargs):
        values = handler_message.text.split()

        if len(values) < kwargs['response_len']:
            bot.send_message(handler_message.from_user.id, 'Указаны не все показатели \u261d\U0001f3fb')
        elif len(values) > kwargs['response_len']:
            bot.send_message(handler_message.from_user.id, 'Указаны лишние показатели \u261d\U0001f3fb')
        elif not all(value.isnumeric() for value in values):
            bot.send_message(
                handler_message.from_user.id,
                'Ответ должен быть количетсвенным и состоять из чисел \u261d\U0001f3fb',
            )
        else:
            department = kwargs['department']

            # TODO: stop using json config (#6)
            # TODO: refactor spreadsheet module (#12)
            status = spredsheet.write_KPI_to_google_sheet(
                manager,
                CONFIG['google']['tables']['KPI']['table'],
                CONFIG['google']['tables']['KPI']['sheets'][department],
                handler_message.from_user.id,
                department,
                kwargs['position'],
                values,
            )

            if status:
                bot.send_message(message.from_user.id, 'Данные внесены \u2705\nХорошего вечера! \U0001f942')
            else:
                bot.send_message(handler_message.from_user.id, 'Вас не добавили в таблицу. Администратор оповещен.')

    kwargs = db.get_employee_department_and_position(cursor, message.from_user.id)
    department = kwargs['department']
    position = kwargs['position']

    try:
        # TODO: messages refactoring (#11)
        if messages.MESSAGES_CONFIG[department][position]:
            kwargs.update(response_len=MESSAGES_CONFIG[department][position]['values_amount'])  # noqa
            message = bot.send_message(message.from_user.id, messages.MESSAGES_CONFIG[department][position]['message'])
            bot.register_next_step_handler(message, kpi_check, **kwargs)
        else:
            bot.send_message(
                message.from_user.id,
                'На данный период ваш KPI не отслеживается ботом \U0001f44c\U0001f3fb',
            )
    except (ValueError, KeyError):
        # TODO: logging (#10)
        bot.send_message(message.from_user.id, 'Что-то пошло не так. Администратор оповещен.')


@bot.message_handler(regexp=r'день\S*')
@user_has_permission
def day_statistic_message_handler(message):
    """TODO"""

    bot.send_message(message.chat.id, text='Выберите отдел', reply_markup=statistic_day_markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith('день'))
def day_statistic_callback(call):
    """TODO"""

    bot.answer_callback_query(
        callback_query_id=call.id,
        text='Минуту, собираю данные.\nОбычно это занимает не больше 5 секунд \U0001f552',
    )

    department = call.data.split()[-1]

    # TODO: stop using json config (#6)
    # TODO: refactor spreadsheet module (#12)
    kpi_daily = spredsheet.get_daily_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department,
    )

    bot.send_message(call.message.chat.id, 'Статистика за день \U0001f4c6')
    result_day = [f'{k}: {v}' for k, v in kpi_daily.items()]
    bot.send_message(call.message.chat.id, '\n'.join(result_day))

    bot.send_message(call.message.chat.id, 'Статистика по сотрудникам \U0001F465')

    # TODO: stop using json config (#6)
    # TODO: refactor spreadsheet module (#12)
    kpi_daily_detail = spredsheet.get_daily_detail_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department
    )
    result_week = []
    for position, employees in kpi_daily_detail.items():
        employees_result = []
        if employees:
            for employee, values in employees.items():
                employees_result.append(f'\n\U0001F464 {employee}:\n')
                employees_result.append('\n'.join([f'{k}: {v}' for k, v in values.items()]))
            result_week.append(f'\n\n\U0001F53D {position.upper()}')
            result_week.append('\n'.join(employees_result))
    bot.send_message(call.message.chat.id, '\n'.join(result_week))


@bot.message_handler(regexp=r'неделя\S*')
@user_has_permission
def week_statistic_message_handler(message):
    """TODO"""

    bot.send_message(message.chat.id, text='Выберите отдел', reply_markup=stat_week_markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith('неделя'))
def week_statistic_callback(call):
    """TODO"""

    bot.answer_callback_query(
        callback_query_id=call.id,
        text=('Собираю данные.\nОбычно это занимает не больше 5 секунд \U0001f552'),
    )

    department = call.data.split()[-1]

    # TODO: stop using json config (#6)
    # TODO: refactor spreadsheet module (#12)
    kpi_daily = spredsheet.get_weekly_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department,
    )

    bot.send_message(call.message.chat.id, 'Статистика за неделю \U0001f5d3')
    result = [f'{k}: {v}' for k, v in kpi_daily.items()]
    bot.send_message(call.message.chat.id, '\n'.join(result))


@bot.message_handler(regexp=r'выручка\S*')
@user_has_permission
@user_is_admin
def day_revenue_message_handler(message):
    """TODO"""

    bot.send_message(message.from_user.id, f'Привет {message.from_user.first_name}!\nКакая сумма выручки на сегодня?')
    bot.register_next_step_handler(message, day_revenue)


def day_revenue(handler_message):
    if not handler_message.text.isnumeric():
        bot.send_message(
            handler_message.from_user.id,
            'Прости, я не понял. Попробуй снова и пришли пожалуйста данные в числовом формате \u261d\U0001f3fb',
        )
    else:
        # TODO: stop using json config (#6)
        # TODO: refactor spreadsheet module (#12)
        status = spredsheet.write_income_to_google_sheet(
            manager,
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets']['руководство'],
            handler_message.text,
        )
        if status:
            bot.send_message(handler_message.from_user.id, 'Спасибо! Данные внесены \u2705')
        else:
            bot.send_message(handler_message.from_user.id, 'Что-то пошло не так. Администратор оповещен.')


@bot.message_handler(regexp=r'иски\S*')
@user_has_permission
@user_is_admin
def start_week_lawsuits(message):
    """TODO"""

    bot.send_message(
        message.from_user.id,
        f'Привет {message.from_user.first_name}!\n'
        'Сколько было подано исков на этой неделе?'
    )
    bot.register_next_step_handler(message, _week_lawsuits)


def _week_lawsuits(message):
    """TODO"""

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
@user_has_permission
def show_the_leader_start_message(message):
    """TODO"""

    bot.send_message(
        message.chat.id,
        text='Выберите отдел',
        reply_markup=leader_markup
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith('красавчик'))
def show_the_leader(call):
    """TODO"""

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
@user_has_permission
@user_is_admin
def start_make_announcement(message):
    """TODO"""

    bot.send_message(
        message.from_user.id,
        f'Привет {message.from_user.first_name}! '
        'Пришли мне текст сообщения, а я отправлю '
        'его всем сотрудникам \U0001f4dd'
    )
    bot.register_next_step_handler(message, _make_announcement)


def _make_announcement(message):
    """TODO"""

    ids = db.return_users_ids(cursor)
    kwargs = {'text': message.text, 'ids': ids}
    bot.send_message(message.from_user.id, 'Записал. Отправляем? (да/нет)')
    bot.register_next_step_handler(message, _send_announcement, **kwargs)


def _send_announcement(message, **kwargs):
    """TODO"""

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
