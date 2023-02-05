import json
import logging
from logging import getLogger

import telebot
from telebot.apihelper import ApiException, ApiTelegramException

import messages
from handlers.kpi_handlers import prepare_kpi_keys_and_questions, update_employee_kpi
from handlers.user_handlers import user_is_registered, user_has_admin_permission, get_users_list, get_user_ids
# from google import spredsheet
from settings import settings

bot = telebot.TeleBot(settings.environments['TELEGRAM_STAFF_TOKEN'])

logger = getLogger(__name__)


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


def handle_callback_by_key(key):
    """TODO"""

    def inner(call):
        try:
            return json.loads(call.data)['key'] == key
        except (ValueError, KeyError):
            return False

    return inner


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
def send_users_list(message):
    """
    /users command handler:
    sends a list of registered users.
    """

    users_list_str = '\n'.join([f'{firstname} {lastname}' for firstname, lastname in get_users_list()])
    text = f'Список пользователей:\n\n' + users_list_str
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

    def parse_answer(answer, kpi_keys: list[str]) -> None:
        values_from_user = answer.text.split()

        if len(values_from_user) != len(kpi_keys):
            bot.send_message(
                answer.from_user.id,
                '\U0000274E - количество показателей не соответствует числу вопросов. Попробуйте еще раз.',
            )
            return

        if list(filter(lambda item: not item.isnumeric(), values_from_user)):
            bot.send_message(
                answer.from_user.id,
                '\U0000274E - неверный формат показателей. Попробуйте еще раз.',
            )
            return

        bot.send_message(answer.from_user.id, '\U0001f552 - вношу данные.')

        data = list(zip(kpi_keys, values_from_user))
        update_employee_kpi(answer.from_user.id, data)
        bot.send_message(answer.from_user.id, '\U00002705 - данные внесены. Хорошего вечера!')
        return


    kpi_keys, kpi_questions = prepare_kpi_keys_and_questions(message.from_user.id)
    if len(kpi_keys) == 0:
        bot.send_message(message.from_user.id, '\U0001F44C - сегодня у вас не нет запланированных отчетов. Спасибо!')
        return

    questions_str = '\n'.join([f'{order + 1}. {question}' for order, question in enumerate(kpi_questions)])
    text = '\U0001F4CB - пришлите следующие количественные данные одним сообщением, согласно приведенному порядку. ' \
           f'Разделяйте числа пробелами:\n\n{questions_str}',
    bot.send_message(message.from_user.id, text)

    bot.register_next_step_handler(message, parse_answer, kpi_keys)


# @bot.message_handler(regexp=r'день\S*')
# @user_has_permission
# def day_statistic_message_handler(message):
#     """
#     Day statistic handler:
#     allows user to get statistics (KPI, leader, and other values) of the chosen department for today.
#     Shows a markup with the departments list, which triggers day_statistic callback.
#     """
#
#     @bot.callback_query_handler(func=lambda c: c.data.startswith('день'))
#     def day_statistic_callback(call):
#         """
#         Day statistic handler's callback:
#         sends user day statistics of the specified department.
#         """
#
#         bot.answer_callback_query(callback_query_id=call.id, text='Собираю данные \U0001f552')
#
#         department = call.data.split()[-1]
#
#         # TODO: stop using json config (#6)
#         # TODO: refactor spreadsheet module (#12)
#         kpi_daily = spredsheet.get_daily_statistic(
#             sheet_key=CONFIG['google']['tables']['KPI']['table'],
#             page_id=CONFIG['google']['tables']['KPI']['sheets'][department],
#             department=department,
#         )
#
#         bot.send_message(call.message.chat.id, 'Статистика за день \U0001f4c6')
#         result_day = [f'{k}: {v}' for k, v in kpi_daily.items()]
#         bot.send_message(call.message.chat.id, '\n'.join(result_day))
#
#         bot.send_message(call.message.chat.id, 'Статистика по сотрудникам \U0001F465')
#
#         # TODO: stop using json config (#6)
#         # TODO: refactor spreadsheet module (#12)
#         kpi_daily_detail = spredsheet.get_daily_detail_statistic(
#             sheet_key=CONFIG['google']['tables']['KPI']['table'],
#             page_id=CONFIG['google']['tables']['KPI']['sheets'][department],
#             department=department
#         )
#         result_week = []
#         for position, employees in kpi_daily_detail.items():
#             employees_result = []
#             if employees:
#                 for employee, values in employees.items():
#                     employees_result.append(f'\n\U0001F464 {employee}:\n')
#                     employees_result.append('\n'.join([f'{k}: {v}' for k, v in values.items()]))
#                 result_week.append(f'\n\n\U0001F53D {position.upper()}')
#                 result_week.append('\n'.join(employees_result))
#         bot.send_message(call.message.chat.id, '\n'.join(result_week))
#
#     reply_markup = telebot.types.InlineKeyboardMarkup()
#     reply_markup.add(
#         telebot.types.InlineKeyboardButton('', callback_data='day-statistic-finances'),
#         telebot.types.InlineKeyboardButton('', callback_data='day-statistic-law'),
#         telebot.types.InlineKeyboardButton('', callback_data='day-statistic-sales'),
#         telebot.types.InlineKeyboardButton('', callback_data='day-statistic-support'),
#     )
#
#     bot.send_message(message.chat.id, text='Выберите отдел', reply_markup=reply_markup)


@bot.message_handler(regexp=r'неделя\S*')
@user_has_permission
def week_statistic_message_handler(message):
    """
    Week statistic handler:
    allows user to get statistics (KPI, leader, and other values) of the chosen department for the current week.
    Shows a markup with the departments list, which triggers week_statistic callback.
    """

    bot.send_message(message.chat.id, text='Выберите отдел', reply_markup=statistic_week_markup)


# @bot.callback_query_handler(func=lambda c: c.data.startswith('неделя'))
# def week_statistic_callback(call):
#     """
#     Week statistic handler's callback:
#     sends user week statistics of the specified department.
#     """
#
#     bot.answer_callback_query(
#         callback_query_id=call.id,
#         text=('Собираю данные.\nОбычно это занимает не больше 5 секунд \U0001f552'),
#     )
#
#     department = call.data.split()[-1]
#
#     # TODO: stop using json config (#6)
#     # TODO: refactor spreadsheet module (#12)
#     kpi_daily = spredsheet.get_weekly_statistic(
#         sheet_key=CONFIG['google']['tables']['KPI']['table'],
#         page_id=CONFIG['google']['tables']['KPI']['sheets'][department],
#         department=department,
#     )
#     bot.send_message(call.message.chat.id, 'Статистика за неделю \U0001f5d3')
#     result = [f'{k}: {v}' for k, v in kpi_daily.items()]
#     bot.send_message(call.message.chat.id, '\n'.join(result))


# @bot.message_handler(regexp=r'выручка\S*')
# @user_has_permission
# @user_is_admin
# def day_revenue_message_handler(message):
#     """
#     Day revenue handler (admin permission required):
#     allows user to send a revenue for today.
#     The provided values are written on the KPI google sheet.
#     """
#
#     def get_day_revenue(handler_message):
#         if not handler_message.text.isnumeric():
#             bot.send_message(
#                 handler_message.from_user.id,
#                 'Прости, я не понял. Попробуй снова и пришли пожалуйста данные в числовом формате \u261d\U0001f3fb',
#             )
#         else:
#             # TODO: stop using json config (#6)
#             # TODO: refactor spreadsheet module (#12)
#             status = spredsheet.write_income_to_google_sheet(
#                 sheet_key=CONFIG['google']['tables']['KPI']['table'],
#                 page_id=CONFIG['google']['tables']['KPI']['sheets']['руководство'],
#                 value=handler_message.text,
#             )
#             if status:
#                 bot.send_message(handler_message.from_user.id, 'Спасибо! Данные внесены \u2705')
#             else:
#                 bot.send_message(handler_message.from_user.id, 'Что-то пошло не так. Администратор оповещен.')
#
#     bot.send_message(message.from_user.id, f'Привет {message.from_user.first_name}!\nКакая сумма выручки на сегодня?')
#     bot.register_next_step_handler(message, get_day_revenue)


# @bot.message_handler(regexp=r'иски\S*')
# @user_has_permission
# @user_is_admin
# def week_lawsuits_message_handler(message):
#     """
#     Week lawsuits handler (admin permission required):
#     allows user to send a number of written lawsuits for today.
#     The provided values are written on the KPI google sheet.
#     """
#
#     def send_week_lawsuits(handler_message):
#         if not handler_message.text.isnumeric():
#             bot.send_message(
#                 handler_message.from_user.id,
#                 'Прости, я не понял. Попробуй снова и пришли пожалуйста данные в числовом формате \u261d\U0001f3fb',
#             )
#         else:
#             # TODO: stop using json config (#6)
#             # TODO: refactor spreadsheet module (#12)
#             status = spredsheet.write_lawsuits_to_google_sheet(
#                 sheet_key=CONFIG['google']['tables']['KPI']['table'],
#                 page_id=CONFIG['google']['tables']['KPI']['sheets']['делопроизводство'],
#                 value=handler_message.text,
#             )
#             if status:
#                 bot.send_message(handler_message.from_user.id, 'Спасибо! Данные внесены \u2705')
#             else:
#                 # TODO: logging (#10)
#                 bot.send_message(handler_message.from_user.id, 'Что-то пошло не так.')
#
#     bot.send_message(
#         message.from_user.id,
#         f'Привет {message.from_user.first_name}!\nСколько было подано исков на этой неделе?',
#     )
#     bot.register_next_step_handler(message, send_week_lawsuits)


@bot.message_handler(regexp=r'красавчик\S*')
@user_has_permission
def day_leader_message_handler(message):
    """
    Day leader handler:
    allows to see the leader (an employee with the best KPI values) of the chosen department for the current day.
    Shows a markup with the departments list, which triggers day_leader callback.
    """

    bot.send_message(message.chat.id, text='Выберите отдел', reply_markup=leader_markup)


# @bot.callback_query_handler(func=lambda c: c.data.startswith('красавчик'))
# def day_leader_callback(call):
#     """
#     Day leader handler's callback:
#     tell who is the leader of the specified department.
#     If there is no leader for today, just sends a corresponding message.
#     """
#
#     department = call.data.split()[-1]
#     # TODO: stop using json config (#6)
#     # TODO: refactor spreadsheet module (#12)
#     leaders = spredsheet.get_leaders_from_google_sheet(
#         sheet_key=CONFIG['google']['tables']['KPI']['table'],
#         page_id=CONFIG['google']['tables']['KPI']['sheets'][department],
#         department=department,
#     )
#     if leaders:
#         bot.send_message(call.message.chat.id, '\U0001f38a Красавчики дня: ' + ', '.join(leaders))
#     else:
#         bot.send_message(call.message.chat.id, '\U0001f5ff Красавчиков дня нет')


@bot.message_handler(regexp=r'объявление\S*')
@user_has_permission
@user_is_admin
def make_announcement_message_handler(message):
    """
    Announcement handler (admin permission required):
    sends an announcement (a message) to all users.
    """

    announcement_text = None
    user_ids_for_announcement = []

    reply_markup = telebot.types.InlineKeyboardMarkup()
    reply_markup.add(
        telebot.types.InlineKeyboardButton(
            text='да',
            callback_data=json.dumps({'key': 'announcement', 'action': 'send'}),
        ),
        telebot.types.InlineKeyboardButton(
            text='отмена',
            callback_data=json.dumps({'key': 'announcement', 'action': 'cancel'}),
        ),
    )

    @bot.callback_query_handler(func=handle_callback_by_key('announcement'))
    def send_announcement(call):
        data = json.loads(call.data)
        if data['action'] == 'send':
            for user_id in user_ids_for_announcement:
                try:
                    bot.send_message(user_id, announcement_text)
                except ApiTelegramException:
                    logger.exception('Sending announcement message to user failed', extra={'user_id': user_id})
            bot.send_message(call.from_user.id, 'Готово! Сотрудники уведомлены \u2705')
        else:
            bot.send_message(call.message.chat.id, 'Отменяю \U0001f44c\U0001f3fb')

    def prepare_announcement(handler_message):
        nonlocal announcement_text

        user_ids_for_announcement.extend(get_user_ids())
        announcement_text = handler_message.text
        bot.send_message(handler_message.from_user.id, 'Записал. Отправляем?', reply_markup=reply_markup)

    bot.send_message(message.from_user.id, f'Привет! Пришли сообщение, которое нужно отправить сотрудникам \U0001f4dd')
    bot.register_next_step_handler(message, prepare_announcement)


if __name__ == '__main__':
    # TODO: investigate logs and try to catch the errors
    # TODO: logging (#10)
    bot.infinity_polling(logger_level=logging.INFO)
