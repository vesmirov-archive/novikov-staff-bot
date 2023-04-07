"""
    Notifies users through a specific way (flags):
    '-c statistics-day' -- send day statistic
    '-c statistics-week' -- send week statistic
    '-c values-reminder' -- send a reminder to enter the statistic values
"""
import argparse
import logging

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from sheets.handlers import statistics, other
from utils import users

from settings import settings

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--action', dest='action')
args = parser.parse_args()


def send_statistics_for_day(bot: TeleBot) -> None:
    """TODO"""

    statistics_data = statistics.get_statistic_for_today()

    statistics_messages_batch = ['\U0001F4C5 - СТАТИСТИКА ЗА ДЕНЬ']

    for section_name, section_data in statistics_data.items():
        section_messages = [f'\n\n{section_name.upper()}\n']

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

        statistics_messages_batch.append('\n'.join(section_messages))

    statistics_result_message = '\n'.join(statistics_messages_batch)

    key_values_data = other.get_key_values()

    key_values_messages_batch = ['\U0001F511 - ДАННЫЕ ПО КЛЮЧЕВЫМ ПОКАЗАТЕЛЯМ\n']
    for key_value_data in key_values_data.values():
        key_values_messages_batch.append(f'{key_value_data["name"].upper()}\n')

        for value in key_value_data['values']:
            period, actual, planned = value
            key_values_messages_batch.append(f'{period}\t\t\tфакт: {actual}\t\t\t{f"план: {planned}" if planned else ""}')
        key_values_messages_batch.append('')

    key_values_result_message = '\n'.join(key_values_messages_batch)

    funds_data = other.get_funds_statistics()

    funds_messages_batch = ['\U0001F4CA - ДАННЫЕ ПО ФОНДАМ\n']
    for fund_name, fund_data in funds_data.items():
        actual, planned = fund_data
        funds_messages_batch.append(f'{fund_name}:')
        funds_messages_batch.append(f'\t\t\tфакт: {actual}')
        funds_messages_batch.append(f'\t\t\tплан: {planned}\n')

    funds_result_message = '\n'.join(funds_messages_batch)

    funds_admin_data = other.get_funds_statistics(full=True)

    funds_admin_messages_batch = ['\U0001F4CA - ДАННЫЕ ПО ФОНДАМ\n']
    for fund_name, fund_data in funds_admin_data.items():
        actual, planned = fund_data
        funds_admin_messages_batch.append(f'{fund_name}:')
        funds_admin_messages_batch.append(f'\t\t\tфакт: {actual}')
        funds_admin_messages_batch.append(f'\t\t\tплан: {planned}\n')

    funds_admin_result_message = '\n'.join(funds_admin_messages_batch)

    leaders_for_today = other.get_leader()
    if not leaders_for_today:
        leaders_for_today_result_message = '\U0001F9E2 - сегодня красавчиков нет.'
    else:
        leaders_for_today_result_message = f'\U0001F451 - красавчики сегодня:\n{", ".join(leaders_for_today)}'

    for user_id in users.get_user_ids():
        sending_to_admin = users.user_has_admin_permission(user_id)
        try:
            bot.send_message(user_id, statistics_result_message)
            bot.send_message(user_id, key_values_result_message)
            bot.send_message(user_id, funds_admin_result_message if sending_to_admin else funds_result_message)
            bot.send_message(user_id, leaders_for_today_result_message)
        except ApiTelegramException:
            logger.exception('Sending scheduled day statistics to user failed', extra={'user_id': user_id})


def send_statistics_for_week(bot: TeleBot) -> None:
    """TODO"""

    ...


def send_statistics_reminder(bot: TeleBot) -> None:
    """TODO"""

    ...


def handle_action() -> None:
    """TODO"""

    bot = TeleBot(settings.telegram_token)

    if args.action == 'statistics-day':
        send_statistics_for_day(bot)
    elif args.action == 'statistics-week':
        send_statistics_for_week(bot)
    elif args.action == 'send-statistics-reminder':
        send_statistics_reminder(bot)


if __name__ == '__main__':
    handle_action()
