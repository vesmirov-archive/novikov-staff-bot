import logging
from functools import wraps
from logging import getLogger
from typing import Callable, Any

import telebot
from telebot.types import Message

from settings import telegram as tele
from utils.users import user_is_registered
from views.commands import send_users_list, send_start_message
from views.handlers.comminication import AnnouncementHandler
from views.handlers.kpi import KPIHandler
from views.handlers.statistics import StatisticsHandler

logger = getLogger(__name__)


# Markups

tele.main_markup.add(
    telebot.types.InlineKeyboardButton('мои показатели \U0001f3af', callback_data='send-kpi-request'),
    telebot.types.InlineKeyboardButton('статистика \U0001F4CA', callback_data='get-statistics-request'),
    telebot.types.InlineKeyboardButton('объявление \U0001f4ef', callback_data='make-announcement-request'),
)


def user_is_authorized(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Permission decorator.
    Checks if the telegram user is registered and has access to the bot.
    Otherwise, sends an error message.
    """

    @wraps(func)
    def wrapper(message: Message):
        if user_is_registered(message.from_user.id):
            func(message)
        else:
            message_text = 'У вас нет прав для взаимодействия с ботом.'
            tele.bot.send_message(message.from_user.id, message_text)

    return wrapper


# Commands actions

@tele.bot.message_handler(commands=['start'])
@user_is_authorized
def start_command_handler(message: Message) -> None:
    """
    /start command handler:
    sends a 'welcome message' and displays a main markup to user
    """

    send_start_message(message)


@tele.bot.message_handler(commands=['users'])
@user_is_authorized
def users_command_handler(message: Message) -> None:
    """
    /users command handler:
    sends a list of registered users.
    """

    send_users_list(message)


# Message actions

@tele.bot.message_handler(regexp=r'мои показатели\S*')
@user_is_authorized
def get_kpi_from_employee(message: Message) -> None:
    """
    KPI handler:
    allows user to send his day results (KPI values).
    The provided values are written on the KPI google sheet.
    """

    KPIHandler(sender_id=message.from_user.id).receive_kpi(message)


@tele.bot.message_handler(regexp=r'статистика\S*')
@user_is_authorized
def send_statistics(message: Message) -> None:
    """TODO"""

    StatisticsHandler(sender_id=message.from_user.id).send_statistics(message)


@tele.bot.message_handler(regexp=r'объявление\S*')
@user_is_authorized
def send_announcement(message: Message) -> None:
    """TODO"""

    AnnouncementHandler(sender_id=message.from_user.id).make_announcement(message)


if __name__ == '__main__':
    tele.bot.infinity_polling(logger_level=logging.WARNING)
