"""
    Notifies users through a specific way (flags):
    '-c statistics-day' -- send day statistic
    '-c statistics-week' -- send week statistic
    '-c values-reminder' -- send a reminder to enter the statistic values
"""
import argparse
import logging

from telebot.apihelper import ApiTelegramException

from settings import telegram as tele
from sheets.handlers import statistics, other
from utils import users
from views.handlers.kpi import KPIHandler
from views.handlers.statistics import StatisticsHandler

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--action', dest='action')
args = parser.parse_args()


def send_statistics_for_day() -> None:
    """TODO"""

    # general values
    general_values_data = statistics.get_statistic_for_today()
    general_values_result_message = StatisticsHandler.build_result_message_general_values_day(data=general_values_data)

    # key values
    key_values_data = statistics.get_key_values()
    key_values_result_message = StatisticsHandler.build_result_message_key_values_accumulative(data=key_values_data)

    # funds fulfillment values
    # TODO: DRY (use the sample above)
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

    # leaders of the day
    # TODO: DRY (use the sample above)
    leaders_for_today = other.get_leader()
    if not leaders_for_today:
        leaders_for_today_result_message = '\U0001F9E2 - сегодня красавчиков нет.'
    else:
        leaders_for_today_result_message = f'\U0001F451 - красавчики сегодня:\n{", ".join(leaders_for_today)}'

    # bonus values
    users_bonus_values = KPIHandler.build_result_message_bonuses()

    for user_id in users.get_statistics_subscribers_list():
        sending_to_admin = users.user_has_admin_permission(user_id)
        try:
            tele.bot.send_message(user_id, general_values_result_message)
            tele.bot.send_message(user_id, key_values_result_message)
            tele.bot.send_message(user_id, funds_admin_result_message if sending_to_admin else funds_result_message)
            tele.bot.send_message(user_id, users_bonus_values)
            tele.bot.send_message(user_id, leaders_for_today_result_message)
        except ApiTelegramException:
            logger.exception('Sending scheduled day statistics to user failed', extra={'user_id': user_id})


def send_statistics_for_week() -> None:
    """TODO"""

    ...


def send_statistics_reminder() -> None:
    """TODO"""

    ...


def handle_action() -> None:
    """TODO"""

    if args.action == 'statistics-day':
        send_statistics_for_day()
    elif args.action == 'statistics-week':
        send_statistics_for_week()
    elif args.action == 'send-statistics-reminder':
        send_statistics_reminder()


if __name__ == '__main__':
    handle_action()
