from logging import getLogger

from settings import telegram as tele
from utils.users import get_users_list

logger = getLogger(__name__)


def send_users_list(message):
    users_list_str = '\n'.join([f'{firstname} {lastname}' for firstname, lastname in get_users_list()])
    text = f'Список пользователей:\n\n' + users_list_str
    tele.bot.send_message(message.from_user.id, text)


def send_start_message(message):
    user_id = message.from_user.id
    message_text = (
        f'Привет, {message.from_user.first_name}! Я бот юридического центра Новиков.\n'
        'Я собираю статистику по сотрудникам и фиксирую данные в Google Sheets.\n'
    )

    tele.bot.send_message(user_id, message_text, reply_markup=tele.main_markup)
