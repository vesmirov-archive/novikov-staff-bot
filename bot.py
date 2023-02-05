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

main_reply_markup = telebot.types.ReplyKeyboardMarkup(row_width=3)
main_reply_markup.add(
    telebot.types.InlineKeyboardButton('мои показатели \U0001f3af'),
    telebot.types.InlineKeyboardButton('статистика \U0001F4CA'),
    telebot.types.InlineKeyboardButton('красавчики \U0001F3C6'),
    telebot.types.InlineKeyboardButton('объявление \U0001f4ef'),
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
def start_command_handler(message):
    """
    /start command handler:
    sends a 'welcome message' and displays a main markup to user
    """

    user_id = message.from_user.id
    name = message.from_user.first_name
    bot.send_message(user_id, messages.START_MESSAGE.format(name), reply_markup=main_reply_markup)


@bot.message_handler(commands=['users'])
@user_has_permission
def users_command_handler(message):
    """
    /users command handler:
    sends a list of registered users.
    """

    users_list_str = '\n'.join([f'{firstname} {lastname}' for firstname, lastname in get_users_list()])
    text = f'Список пользователей:\n\n' + users_list_str
    bot.send_message(message.from_user.id, text)


# Message actions

@bot.message_handler(regexp=r'мои показатели\S*')
@user_has_permission
def send_kpi_message_handler(message):
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


@bot.message_handler(regexp=r'статистика\S*')
@user_has_permission
def statistics_message_handler(message):
    """
    Day statistic handler:
    allows user to get statistics (KPI, leader, and other values) of the chosen department for today.
    Shows a markup with the departments list, which triggers day_statistic callback.
    """

    reply_markup_day_statistics = telebot.types.InlineKeyboardMarkup()
    reply_markup_day_statistics.add(
        telebot.types.InlineKeyboardButton(
            text='финансы',
            callback_data=json.dumps({'key': 'day-statistic', 'data': {'section': 'finances'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='делопроизводство',
            callback_data=json.dumps({'key': 'day-statistic', 'data': {'section': 'law'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='продажи',
            callback_data=json.dumps({'key': 'day-statistic', 'data': {'section': 'sales'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='поддержка',
            callback_data=json.dumps({'key': 'day-statistic', 'data': {'section': 'support'}}),
        ),
    )

    reply_markup_week_statistics = telebot.types.InlineKeyboardMarkup()
    reply_markup_week_statistics.add(
        telebot.types.InlineKeyboardButton(
            text='финансы',
            callback_data=json.dumps({'key': 'week-statistic', 'data': {'section': 'finances'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='делопроизводство',
            callback_data=json.dumps({'key': 'week-statistic', 'data': {'section': 'law'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='продажи',
            callback_data=json.dumps({'key': 'week-statistic', 'data': {'section': 'sales'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='поддержка',
            callback_data=json.dumps({'key': 'week-statistic', 'data': {'section': 'support'}}),
        ),
    )

    @bot.callback_query_handler(func=handle_callback_by_key('day-statistic'))
    def day_statistic_callback(call):
        """
        Day statistic handler's callback:
        sends user day statistics for the specified section.
        """

        bot.send_message(call.message.chat.id, '\U0001f552 - cобираю данные.')

        callback_data = json.loads(call.data)
        section = callback_data['data']['section']

        ...

    @bot.callback_query_handler(func=handle_callback_by_key('week-statistic'))
    def week_statistic_callback(call):
        """
        Week statistic handler's callback:
        sends user week statistics for the specified section.
        """

        bot.send_message(call.message.chat.id, '\U0001f552 - cобираю данные.')

        callback_data = json.loads(call.data)
        section = callback_data['data']['section']

        ...

    bot.send_message(
        message.chat.id,
        text='\U0001F520 - выберите направление',
        reply_markup=reply_markup_day_statistics,
    )


# @bot.message_handler(regexp=r'красавчик\S*')
# @user_has_permission
# def day_leader_message_handler(message):
#     """
#     Day leader handler:
#     allows to see the leader (an employee with the best KPI values) of the chosen department for the current day.
#     Shows a markup with the departments list, which triggers day_leader callback.
#     """
#     leader_markup = telebot.types.InlineKeyboardMarkup()
#     leader_markup.add(
#         telebot.types.InlineKeyboardButton('делопроизводство', callback_data='красавчик делопроизводство'),
#     )
#
#     @bot.callback_query_handler(func=lambda c: c.data.startswith('красавчик'))
#     def day_leader_callback(call):
#         """
#         Day leader handler's callback:
#         tell who is the leader of the specified department.
#         If there is no leader for today, just sends a corresponding message.
#         """
#
#         department = call.data.split()[-1]
#         # TODO: stop using json config (#6)
#         # TODO: refactor spreadsheet module (#12)
#         leaders = spredsheet.get_leaders_from_google_sheet(
#             sheet_key=CONFIG['google']['tables']['KPI']['table'],
#             page_id=CONFIG['google']['tables']['KPI']['sheets'][department],
#             department=department,
#         )
#         if leaders:
#             bot.send_message(call.message.chat.id, '\U0001f38a Красавчики дня: ' + ', '.join(leaders))
#         else:
#             bot.send_message(call.message.chat.id, '\U0001f5ff Красавчиков дня нет')
#
#     bot.send_message(message.chat.id, text='Выберите отдел', reply_markup=leader_markup)


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
            callback_data=json.dumps({'key': 'announcement', 'data': {'action': 'send'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='отмена',
            callback_data=json.dumps({'key': 'announcement', 'data': {'action': 'cancel'}}),
        ),
    )

    @bot.callback_query_handler(func=handle_callback_by_key('announcement'))
    def send_announcement(call):
        callback_data = json.loads(call.data)
        if callback_data['data']['action'] == 'send':
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
    bot.infinity_polling(logger_level=logging.WARNING)
