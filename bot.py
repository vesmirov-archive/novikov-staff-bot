import json
import logging
from logging import getLogger

import telebot

import messages
from handlers.sheets.other_handlers import get_key_values, get_funds_statistics, get_leader
from handlers.sheets.statistics_handlers import get_statistic_for_today
from handlers.sheets.statistics_handlers import prepare_kpi_keys_and_questions, update_employee_kpi
from handlers.sheets.user_handlers import (user_is_registered, user_has_admin_permission, get_users_list, get_user_ids,
                                           get_user_full_name_from_id)
from settings import settings

bot = telebot.TeleBot(settings.environments['TELEGRAM_STAFF_TOKEN'])

logger = getLogger(__name__)


# Markups

main_reply_markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
main_reply_markup.add(
    telebot.types.InlineKeyboardButton('мои показатели \U0001f3af'),
    telebot.types.InlineKeyboardButton('статистика \U0001F4CA'),
    telebot.types.InlineKeyboardButton('объявление \U0001f4ef'),
    telebot.types.InlineKeyboardButton('другое \U00002795'),
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
    TODO
    """

    reply_markup_choose_period = telebot.types.InlineKeyboardMarkup(row_width=2)
    reply_markup_choose_period.add(
        telebot.types.InlineKeyboardButton(
            text='день',
            callback_data=json.dumps({'key': 'statistics', 'data': {'period': 'day'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='неделя',
            callback_data=json.dumps({'key': 'statistics', 'data': {'period': 'week'}}),
        )
    )

    reply_markup_day_statistics = telebot.types.InlineKeyboardMarkup(row_width=2)
    reply_markup_day_statistics.add(
        telebot.types.InlineKeyboardButton(
            text='финансы',
            callback_data=json.dumps({'key': 'day-statistics', 'data': {'section': 'finances'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='делопроизводство',
            callback_data=json.dumps({'key': 'day-statistics', 'data': {'section': 'law'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='продажи',
            callback_data=json.dumps({'key': 'day-statistics', 'data': {'section': 'sales'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='поддержка',
            callback_data=json.dumps({'key': 'day-statistics', 'data': {'section': 'support'}}),
        ),
    )

    reply_markup_week_statistics = telebot.types.InlineKeyboardMarkup(row_width=2)
    reply_markup_week_statistics.add(
        telebot.types.InlineKeyboardButton(
            text='финансы',
            callback_data=json.dumps({'key': 'week-statistics', 'data': {'section': 'finances'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='делопроизводство',
            callback_data=json.dumps({'key': 'week-statistics', 'data': {'section': 'law'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='продажи',
            callback_data=json.dumps({'key': 'week-statistics', 'data': {'section': 'sales'}}),
        ),
        telebot.types.InlineKeyboardButton(
            text='поддержка',
            callback_data=json.dumps({'key': 'week-statistics', 'data': {'section': 'support'}}),
        ),
    )

    @bot.callback_query_handler(func=handle_callback_by_key('day-statistics'))
    def day_statistic_callback(call):
        """
        Day statistic handler's callback:
        sends user day statistics for the specified section.
        """

        bot.send_message(call.message.chat.id, '\U0001f552 - cобираю данные за день.')

        callback_data = json.loads(call.data)
        section = callback_data['data']['section']

        data = get_statistic_for_today(filter_by_section=section)

        messages_batch = ['\U0001F4C5 - СТАТИСТИКА ЗА ДЕНЬ\n']

        for section_name, section_data in data.items():
            section_messages = [f'{section_name.capitalize()}\n\n']

            section_messages.append('\U000027A1 - Суммарно\n')
            for statistic_item in section_data['total']:
                name, value = statistic_item
                section_messages.append(f'{name.capitalize()}: {value}')

            section_messages.append('\n\U000027A1 - По сотрудникам')
            for statistic_item_name, employees_list in section_data['per_employee'].items():
                section_messages.append(f'\n{statistic_item_name.capitalize()}')
                for employee in employees_list:
                    employee_name, value = employee
                    section_messages.append(f'\t\t\t{employee_name}: {value}')

            messages_batch.append('\n'.join(section_messages))

        result_message = '\n'.join(messages_batch)
        bot.send_message(call.message.chat.id, result_message)

    @bot.callback_query_handler(func=handle_callback_by_key('week-statistics'))
    def week_statistic_callback(call):
        """
        Week statistic handler's callback:
        sends user week statistics for the specified section.
        """

        bot.send_message(call.message.chat.id, '\U0001f552 - cобираю данные.')

        callback_data = json.loads(call.data)
        section = callback_data['data']['section']

        data = ...

        messages_batch = ['\U0001F4C6 - СТАТИСТИКА ЗА НЕДЕЛЮ\n\n']
        ...

    @bot.callback_query_handler(func=handle_callback_by_key('statistics'))
    def choose_section_callback(call):
        callback_data = json.loads(call.data)
        period = callback_data['data']['period']

        bot.send_message(
            message.chat.id,
            text='\U0001F520 - выберите направление',
            reply_markup=reply_markup_day_statistics if period == 'day' else reply_markup_week_statistics,
        )

    bot.send_message(
        message.chat.id,
        text='\U0001F5D3 - выберите период',
        reply_markup=reply_markup_choose_period,
    )


@bot.message_handler(regexp=r'объявление\S*')
@user_has_permission
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
                except telebot.apihelper.ApiTelegramException:
                    logger.exception('Sending announcement message to user failed', extra={'user_id': user_id})
            bot.send_message(call.from_user.id, '\U00002705 - готово, сообщение отправлено всем сотрудникам!')
        else:
            bot.send_message(call.message.chat.id, '\U0000274E - отменяю.')

    def prepare_announcement(handler_message):
        nonlocal announcement_text

        sender_full_name = ' '.join(get_user_full_name_from_id(handler_message.from_user.id))
        user_ids_for_announcement.extend(get_user_ids())
        announcement_text = f'Отправитель: {sender_full_name}\n' + handler_message.text
        bot.send_message(
            handler_message.from_user.id,
            '\U0001f44c\U0001f3fb - записал. Отправляем?',
            reply_markup=reply_markup,
        )

    bot.send_message(
        message.from_user.id,
        f'\U0001f4dd - пришли текст сообщения, которое нужно отправить всем сотрудникам.',
    )
    bot.register_next_step_handler(message, prepare_announcement)


@bot.message_handler(regexp=r'другое\S*')
@user_has_permission
def other_message_handler(message):
    """TODO"""

    reply_markup_other = telebot.types.InlineKeyboardMarkup(row_width=1)
    reply_markup_other.add(
        telebot.types.InlineKeyboardButton(
            text='показать наполняемость фондов',
            callback_data=json.dumps({'key': 'other-funds'}),
        ),
        telebot.types.InlineKeyboardButton(
            text='показать статус по ключевым показателям',
            callback_data=json.dumps({'key': 'other-key_values'}),
        ),
        telebot.types.InlineKeyboardButton(
            text='показать красавчика за сегодня',
            callback_data=json.dumps({'key': 'other-leader'}),
        ),
    )

    @bot.callback_query_handler(func=handle_callback_by_key('other-funds'))
    def show_funds_fulfillment_callback(call):
        bot.send_message(call.message.chat.id, '\U0001f552 - cобираю данные.')
        funds_data = get_funds_statistics(call.message.chat.id)

        message_text = ['\U0001F4CA - ДАННЫЕ ПО ФОНДАМ\n']
        for fund_name, fund_data in funds_data.items():
            actual, planned = fund_data
            message_text.append(f'{fund_name}:')
            message_text.append(f'\t\t\tфакт: {actual}')
            message_text.append(f'\t\t\tплан: {planned}\n')

        bot.send_message(call.message.chat.id, '\n'.join(message_text))

    @bot.callback_query_handler(func=handle_callback_by_key('other-key_values'))
    def show_key_values_fulfillment_callback(call):
        bot.send_message(call.message.chat.id, '\U0001f552 - cобираю данные.')
        key_values_data = get_key_values()

        message_text = ['\U0001F511 - ДАННЫЕ ПО КЛЮЧЕВЫМ ПОКАЗАТЕЛЯМ\n']
        for key_value_data in key_values_data.values():
            message_text.append(f'{key_value_data["name"].upper()}\n')

            for value in key_value_data['values']:
                period, actual, planned = value
                message_text.append(f'{period}\t\t\tфакт: {actual}\t\t\t{f"план: {planned}" if planned else ""}')
            message_text.append('')

        bot.send_message(call.message.chat.id, '\n'.join(message_text))

    @bot.callback_query_handler(func=handle_callback_by_key('other-leader'))
    def show_the_leader_for_today(call):
        bot.send_message(call.message.chat.id, '\U0001f552 - cобираю данные.')
        leaders_for_today = get_leader()
        if not leaders_for_today:
            bot.send_message(call.message.chat.id, '\U0001F9E2 - сегодня красавчиков нет.')
        else:
            bot.send_message(call.message.chat.id, f'\U0001F451 - красавчики сегодня:\n{", ".join(leaders_for_today)}')

    bot.send_message(
        message.chat.id,
        text='\U00002754 - выберите действие',
        reply_markup=reply_markup_other,
    )


if __name__ == '__main__':
    bot.infinity_polling(logger_level=logging.WARNING)
