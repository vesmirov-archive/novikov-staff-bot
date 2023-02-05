import time

import telebot

import messages
from services import db
from google import spredsheet
from settings import settings
from handlers.kpi_handlers import prepare_kpi_keys_and_questions, send_kpi_to_google
from handlers.user_handlers import user_is_registered, user_has_admin_permission

bot = telebot.TeleBot(settings.environments['TELEGRAM_STAFF_TOKEN'])


# Markups

main_menu_markup = telebot.types.ReplyKeyboardMarkup(row_width=3)
main_menu_markup.add(
    telebot.types.InlineKeyboardButton('мои показатели \U0001f3af'),
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

statistic_week_markup = telebot.types.InlineKeyboardMarkup()
statistic_week_markup.add(
    telebot.types.InlineKeyboardButton('продажи', callback_data='неделя продажи'),
    telebot.types.InlineKeyboardButton('делопроизводство', callback_data='неделя делопроизводство'),
    telebot.types.InlineKeyboardButton('руководство', callback_data='неделя руководство'),
)

leader_markup = telebot.types.InlineKeyboardMarkup()
leader_markup.add(
    telebot.types.InlineKeyboardButton('делопроизводство', callback_data='красавчик делопроизводство'),
)

plan_markup = telebot.types.InlineKeyboardMarkup()
plan_markup.add(
    telebot.types.InlineKeyboardButton('на день', callback_data='план день'),
    telebot.types.InlineKeyboardButton('на неделю', callback_data='план неделя'),
)


# Permissions

def user_has_permission(func):
    """
    Permission decorator.
    Checks if the telegram user is registered and has access to the bot.
    Otherwise, sends an error message.
    """

    def inner(message):
        if user_is_registered(message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, messages.DENY_ANONIMUS_MESSAGE)
    return inner


def user_is_admin(func):
    """
    Permission decorator.
    Checks if the telegram user is admin.
    Otherwise, sends an error message.
    """

    def inner(message):
        if user_has_admin_permission(message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, messages.DENY_MESSAGE)
    return inner


# Commands actions

@bot.message_handler(commands=['start'])
@user_has_permission
def send_welcome(message):
    """
    /start command handler:
    sends a 'welcome message' and displays a main markup to user
    """

    user_id = message.from_user.id
    name = message.from_user.first_name
    bot.send_message(user_id, messages.START_MESSAGE.format(name), reply_markup=main_menu_markup)

@bot.message_handler(commands=['users'])
@user_has_permission
def send_list_users(message):
    """
    /users command handler:
    sends a list of registered users.
    """

    text = f'Список пользователей:\n' + '\n'.join(f'{}{}')
    bot.send_message(message.from_user.id, text)

# Buttons actions

@bot.message_handler(regexp=r'мои показатели\S*')
@user_has_permission
def kpi_send_message(message):
    """
    KPI handler:
    allows user to send his day results (KPI values).
    The provided values are written on the KPI google sheet.
    """

    def parse_answer(answer, kpi_keys) -> None:
        if not answer.text.isnumeric():
            bot.send_message(
                answer.from_user.id,
                'Неверный формат показателей. Попробуйте еще раз.',
            )
            return

        kpi_values = message.text.split()

        if len(kpi_values) != len(kpi_keys):
            bot.send_message(
                answer.from_user.id,
                'Количество показателей не соответствует числу вопросов. Попробуйте еще раз.',
            )
            return

        succeed = send_kpi_to_google(answer.from_user.id, kpi_values)
        if succeed:
            text = 'Ваши данные внесены. Хорошего вечера!'
        else:
            text = 'Во время отправки данных что-то пошло не так. Ваши данные сохранены. Разработчики уведомлены.'

        bot.send_message(answer.from_user.id, text)
        return


    kpi_keys, kpi_questions = prepare_kpi_keys_and_questions(message.from_user.id)
    if len(kpi_keys) == 0:
        bot.send_message(message.from_user.id, 'Сегодня у вас не нет запланированных отчетов. Спасибо!')
        return

    questions_str = '\n'.join([f'{order}. {question}' for order, question in enumerate(kpi_questions)])
    text = 'Пришлите следующие количественные данные одним сообщением, согласно приведенному порядку. ' \
           f'Разделяйте числа пробелами:\n\n{questions_str}',
    bot.send_message(message.from_user.id, text)

    bot.register_next_step_handler(message, parse_answer, kpi_keys)


@bot.message_handler(regexp=r'день\S*')
@user_has_permission
def day_statistic_message_handler(message):
    """
    Day statistic handler:
    allows user to get statistics (KPI, leader, and other values) of the chosen department for today.
    Shows a markup with the departments list, which triggers day_statistic callback.
    """

    bot.send_message(message.chat.id, text='Выберите отдел', reply_markup=statistic_day_markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith('день'))
def day_statistic_callback(call):
    """
    Day statistic handler's callback:
    sends user day statistics of the specified department.
    """

    bot.answer_callback_query(
        callback_query_id=call.id,
        text='Минуту, собираю данные.\nОбычно это занимает не больше 5 секунд \U0001f552',
    )

    department = call.data.split()[-1]

    # TODO: stop using json config (#6)
    # TODO: refactor spreadsheet module (#12)
    kpi_daily = spredsheet.get_daily_statistic(
        sheet_key=CONFIG['google']['tables']['KPI']['table'],
        page_id=CONFIG['google']['tables']['KPI']['sheets'][department],
        department=department,
    )

    bot.send_message(call.message.chat.id, 'Статистика за день \U0001f4c6')
    result_day = [f'{k}: {v}' for k, v in kpi_daily.items()]
    bot.send_message(call.message.chat.id, '\n'.join(result_day))

    bot.send_message(call.message.chat.id, 'Статистика по сотрудникам \U0001F465')

    # TODO: stop using json config (#6)
    # TODO: refactor spreadsheet module (#12)
    kpi_daily_detail = spredsheet.get_daily_detail_statistic(
        sheet_key=CONFIG['google']['tables']['KPI']['table'],
        page_id=CONFIG['google']['tables']['KPI']['sheets'][department],
        department=department
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
    """
    Week statistic handler:
    allows user to get statistics (KPI, leader, and other values) of the chosen department for the current week.
    Shows a markup with the departments list, which triggers week_statistic callback.
    """

    bot.send_message(message.chat.id, text='Выберите отдел', reply_markup=statistic_week_markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith('неделя'))
def week_statistic_callback(call):
    """
    Week statistic handler's callback:
    sends user week statistics of the specified department.
    """

    bot.answer_callback_query(
        callback_query_id=call.id,
        text=('Собираю данные.\nОбычно это занимает не больше 5 секунд \U0001f552'),
    )

    department = call.data.split()[-1]

    # TODO: stop using json config (#6)
    # TODO: refactor spreadsheet module (#12)
    kpi_daily = spredsheet.get_weekly_statistic(
        sheet_key=CONFIG['google']['tables']['KPI']['table'],
        page_id=CONFIG['google']['tables']['KPI']['sheets'][department],
        department=department,
    )
    bot.send_message(call.message.chat.id, 'Статистика за неделю \U0001f5d3')
    result = [f'{k}: {v}' for k, v in kpi_daily.items()]
    bot.send_message(call.message.chat.id, '\n'.join(result))


@bot.message_handler(regexp=r'выручка\S*')
@user_has_permission
@user_is_admin
def day_revenue_message_handler(message):
    """
    Day revenue handler (admin permission required):
    allows user to send a revenue for today.
    The provided values are written on the KPI google sheet.
    """

    def get_day_revenue(handler_message):
        if not handler_message.text.isnumeric():
            bot.send_message(
                handler_message.from_user.id,
                'Прости, я не понял. Попробуй снова и пришли пожалуйста данные в числовом формате \u261d\U0001f3fb',
            )
        else:
            # TODO: stop using json config (#6)
            # TODO: refactor spreadsheet module (#12)
            status = spredsheet.write_income_to_google_sheet(
                sheet_key=CONFIG['google']['tables']['KPI']['table'],
                page_id=CONFIG['google']['tables']['KPI']['sheets']['руководство'],
                value=handler_message.text,
            )
            if status:
                bot.send_message(handler_message.from_user.id, 'Спасибо! Данные внесены \u2705')
            else:
                bot.send_message(handler_message.from_user.id, 'Что-то пошло не так. Администратор оповещен.')

    bot.send_message(message.from_user.id, f'Привет {message.from_user.first_name}!\nКакая сумма выручки на сегодня?')
    bot.register_next_step_handler(message, get_day_revenue)


@bot.message_handler(regexp=r'иски\S*')
@user_has_permission
@user_is_admin
def week_lawsuits_message_handler(message):
    """
    Week lawsuits handler (admin permission required):
    allows user to send a number of written lawsuits for today.
    The provided values are written on the KPI google sheet.
    """

    def send_week_lawsuits(handler_message):
        if not handler_message.text.isnumeric():
            bot.send_message(
                handler_message.from_user.id,
                'Прости, я не понял. Попробуй снова и пришли пожалуйста данные в числовом формате \u261d\U0001f3fb',
            )
        else:
            # TODO: stop using json config (#6)
            # TODO: refactor spreadsheet module (#12)
            status = spredsheet.write_lawsuits_to_google_sheet(
                sheet_key=CONFIG['google']['tables']['KPI']['table'],
                page_id=CONFIG['google']['tables']['KPI']['sheets']['делопроизводство'],
                value=handler_message.text,
            )
            if status:
                bot.send_message(handler_message.from_user.id, 'Спасибо! Данные внесены \u2705')
            else:
                # TODO: logging (#10)
                bot.send_message(handler_message.from_user.id, 'Что-то пошло не так.')

    bot.send_message(
        message.from_user.id,
        f'Привет {message.from_user.first_name}!\nСколько было подано исков на этой неделе?',
    )
    bot.register_next_step_handler(message, send_week_lawsuits)


@bot.message_handler(regexp=r'красавчик\S*')
@user_has_permission
def day_leader_message_handler(message):
    """
    Day leader handler:
    allows to see the leader (an employee with the best KPI values) of the chosen department for the current day.
    Shows a markup with the departments list, which triggers day_leader callback.
    """

    bot.send_message(message.chat.id, text='Выберите отдел', reply_markup=leader_markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith('красавчик'))
def day_leader_callback(call):
    """
    Day leader handler's callback:
    tell who is the leader of the specified department.
    If there is no leader for today, just sends a corresponding message.
    """

    department = call.data.split()[-1]
    # TODO: stop using json config (#6)
    # TODO: refactor spreadsheet module (#12)
    leaders = spredsheet.get_leaders_from_google_sheet(
        sheet_key=CONFIG['google']['tables']['KPI']['table'],
        page_id=CONFIG['google']['tables']['KPI']['sheets'][department],
        department=department,
    )
    if leaders:
        bot.send_message(call.message.chat.id, '\U0001f38a Красавчики дня: ' + ', '.join(leaders))
    else:
        bot.send_message(call.message.chat.id, '\U0001f5ff Красавчиков дня нет')


@bot.message_handler(regexp=r'объявление\S*')
@user_has_permission
@user_is_admin
def make_announcement_message_handler(message):
    """
    Announcement handler (admin permission required):
    sends an announcement (a message) to all users.
    """

    def send_announcement(handler_message, **kwargs):
        if handler_message.text.lower() == 'нет':
            bot.send_message(handler_message.from_user.id, 'Принял. Отменяю \U0001f44c\U0001f3fb')
        elif handler_message.text.lower() == 'да':
            # TODO: there is a bug - if some user from the DB has 'stopped' the bot, this function will return an error.
            for user_id in kwargs['ids']:
                bot.send_message(user_id, kwargs['text'])
            bot.send_message(handler_message.from_user.id, 'Готово! Сотрудники уведомлены \u2705')
        else:
            bot.send_message(message.from_user.id, 'Я не понял ответа. Отменяю. \U0001f44c\U0001f3fb')

    def prepare_announcement(handler_message):
        ids = db.return_users_ids(cursor)
        kwargs = {'text': handler_message.text, 'ids': ids}
        bot.send_message(handler_message.from_user.id, 'Записал. Отправляем? (да/нет)')
        bot.register_next_step_handler(handler_message, send_announcement, **kwargs)

    bot.send_message(
        message.from_user.id,
        f'Привет {message.from_user.first_name}! Пришли сообщение, которое нужно отправить сотрудникам \U0001f4dd')
    bot.register_next_step_handler(message, prepare_announcement)


if __name__ == '__main__':
    # TODO: investigate logs and try to catch the errors
    # TODO: logging (#10)
    while True:
        try:
            bot.polling()
        except Exception:
            time.sleep(5)
