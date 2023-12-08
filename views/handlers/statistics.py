from typing import Any

from telebot.types import Message, ReplyKeyboardMarkup, InlineKeyboardButton

from settings import settings, telegram as tele
from sheets.handlers.other import get_funds_statistics, get_leader
from sheets.handlers.statistics import get_statistic_accumulate, get_statistic_for_today, get_key_values
from utils.users import user_has_admin_permission


class StatisticsHandler:
    """TODO"""

    STATISTICS_CHOICES = {
        'general_values': '\U0001f4bc - основные показатели',
        'key_values':  '\U0001f511 - ключевые показатели',
        'funds_fulfillment': '\U0001f4ca - наполняемость фондов',
        'leader': '\U0001f451 - красавчик',
        'main_menu':  '\U000021a9\U0000fe0f - главное меню',
    }
    PERIOD_CHOICES = {
        'day': '\U00000031\U0000FE0F\U000020E3 - день',
        'week': '\U00000037\U0000FE0F\U000020E3 - неделя',
        'month': '\U0001f522 - месяц',
        'accumulative': '\U0001F520 - акумулятивно',
    }
    SECTION_CHOICES = {section: f"\U0001f5c2 - {data['name']}" for section, data in settings.config['sections'].items()}

    PERIOD_PER_STATISTICS_CHOICES = {
        'general_values': ['day', 'accumulative'],
        'key_values': ['accumulative'],
        'funds_fulfillment': ['month'],
        'leader': ['day'],
    }

    def __init__(self, sender_id: str):
        self.sender_id = sender_id
        self.statistics_markup = ReplyKeyboardMarkup(row_width=2)
        for text in self.STATISTICS_CHOICES.values():
            self.statistics_markup.add(InlineKeyboardButton(text=text))

        self.section_markup = ReplyKeyboardMarkup(row_width=2)
        for text in self.SECTION_CHOICES.values():
            self.section_markup.add(InlineKeyboardButton(text=text))

    def _choose_section(self, message: Message) -> None:
        if message.text not in self.SECTION_CHOICES.values():
            tele.bot.send_message(
                self.sender_id,
                text='\U00002b07\U0000fe0f - выберите направление',
                reply_markup=self.section_markup,
            )
            tele.bot.register_next_step_handler(message, self._choose_section)
        else:
            # TODO: this crunch can be fixed when the custom Message with `meta` parameter will be implemented
            target_section = None
            for section, section_message in self.SECTION_CHOICES.items():
                if section_message == message.text:
                    target_section = section

            tele.bot.send_message(
                self.sender_id,
                text='\U0001F5D3 - выберите период',
                reply_markup=self._get_period_markup_for_statistics_type('general_values'),
            )

            tele.bot.register_next_step_handler(
                message,
                self._get_general_values_period_handler,
                section_id=target_section,
            )

    def _choose_statistics_type(self, message: Message) -> None:
        if message.text == self.STATISTICS_CHOICES['general_values']:
            tele.bot.send_message(
                self.sender_id,
                text='\U00002b07\U0000fe0f - выберите направление',
                reply_markup=self.section_markup,
            )
            tele.bot.register_next_step_handler(message, self._choose_section)
        elif message.text == self.STATISTICS_CHOICES['key_values']:
            tele.bot.send_message(
                self.sender_id,
                text='\U0001F5D3 - выберите период',
                reply_markup=self._get_period_markup_for_statistics_type('key_values'),
            )
            tele.bot.register_next_step_handler(message, self._get_key_values_period_handler)
        elif message.text == self.STATISTICS_CHOICES['funds_fulfillment']:
            tele.bot.send_message(
                self.sender_id,
                text='\U0001F5D3 - выберите период',
                reply_markup=self._get_period_markup_for_statistics_type('funds_fulfillment'),
            )
            tele.bot.register_next_step_handler(message, self._get_budget_fulfillment_values_period_handler)
        elif message.text == self.STATISTICS_CHOICES['leader']:
            tele.bot.send_message(
                self.sender_id,
                text='\U0001F5D3 - выберите период',
                reply_markup=self._get_period_markup_for_statistics_type('leader'),
            )
            tele.bot.register_next_step_handler(message, self._get_leader_period_handler)
        elif message.text == self.STATISTICS_CHOICES['main_menu']:
            tele.bot.send_message(
                self.sender_id,
                '\U000021a9\U0000fe0f - возврат в главное меню.',
                reply_markup=tele.main_markup,
            )
        else:
            tele.bot.send_message(self.sender_id, '\U00002b07\U0000fe0f - выберите действие.')
            tele.bot.register_next_step_handler(message, self._choose_statistics_type)

    def _get_period_markup_for_statistics_type(self, statistics_type: str) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(row_width=2)
        for period in self.PERIOD_PER_STATISTICS_CHOICES[statistics_type]:
            markup.add(InlineKeyboardButton(text=self.PERIOD_CHOICES[period]))

        return markup

    def _get_general_values_period_handler(self, message: Message, section_id: str) -> None:
        if message.text == self.PERIOD_CHOICES['day']:
            self.send_general_values_day(section_id=section_id)
        # elif message.text == self.PERIOD_CHOICES['week']:
        #     self.send_general_values_week(section_id=section_id)
        elif message.text == self.PERIOD_CHOICES['accumulative']:
            self.send_general_values_accumulative(section_id=section_id)
        else:
            tele.bot.send_message(self.sender_id, '\U0001F5D3 - выберите период.')
            tele.bot.register_next_step_handler(message, self._get_general_values_period_handler)

    def _get_budget_fulfillment_values_period_handler(self, message: Message) -> None:
        if message.text == self.PERIOD_CHOICES['month']:
            self.send_month_funds_fulfillment_values()
        else:
            tele.bot.send_message(self.sender_id, '\U0001F5D3 - выберите период.')
            tele.bot.register_next_step_handler(message, self._get_budget_fulfillment_values_period_handler)

    def _get_leader_period_handler(self, message: Message) -> None:
        if message.text == self.PERIOD_CHOICES['day']:
            self.send_leader_day()
        else:
            tele.bot.send_message(self.sender_id, '\U0001F5D3 - выберите период.')
            tele.bot.register_next_step_handler(message, self._get_leader_period_handler)

    def _get_key_values_period_handler(self, message: Message) -> None:
        if message.text == self.PERIOD_CHOICES['accumulative']:
            self.send_key_values_accumulative()
        else:
            tele.bot.send_message(self.sender_id, '\U0001F5D3 - выберите период.')
            tele.bot.register_next_step_handler(message, self._get_key_values_period_handler)

    @staticmethod
    def build_result_message_key_values_accumulative(data: dict[str, dict[str, tuple[str, str, str]]]):
        messages_batch = ['\U0001F511 - ДАННЫЕ ПО КЛЮЧЕВЫМ ПОКАЗАТЕЛЯМ\n']
        for key_value_data in data.values():
            messages_batch.append(f'\U0001f4cb - {key_value_data["name"].upper()}\n')

            for value in key_value_data['values']:
                period, actual, planned = value
                messages_batch.append(f'{period} -> [факт] {actual} {f": {planned} [план]" if planned else ""}')
            messages_batch.append('')
        return '\n'.join(messages_batch)

    def send_key_values_accumulative(self) -> None:
        tele.bot.send_message(self.sender_id, '\U0001f552 - cобираю данные, подождите.')

        key_values_data = get_key_values()
        result_message = self.build_result_message_key_values_accumulative(key_values_data)

        tele.bot.send_message(self.sender_id, result_message, reply_markup=tele.main_markup)

    def send_leader_day(self) -> None:
        tele.bot.send_message(self.sender_id, '\U0001f552 - cобираю данные, подождите.')
        leaders_for_today = get_leader()

        if leaders_for_today:
            message_text = f'\U0001F451 - красавчики дня:\n{", ".join(leaders_for_today)}'
        else:
            message_text = '\U0001F9E2 - красавчиков дня нет.'

        tele.bot.send_message(self.sender_id, message_text, reply_markup=tele.main_markup)

    def send_month_funds_fulfillment_values(self) -> None:
        tele.bot.send_message(self.sender_id, '\U0001f552 - cобираю данные, подождите.')

        requested_by_admin = user_has_admin_permission(self.sender_id)
        funds_data = get_funds_statistics(full=True if requested_by_admin else False)

        message_text = ['\U0001F4CA - ДАННЫЕ ПО ФОНДАМ\n']
        for fund_name, fund_data in funds_data.items():
            actual, planned = fund_data
            message_text.append(f'{fund_name}:')
            message_text.append(f'[факт] {actual} : {planned} [план]\n')

        tele.bot.send_message(self.sender_id, '\n'.join(message_text), reply_markup=tele.main_markup)

    # TODO: implement weekly statistics functionality
    def send_general_values_week(self, section_id=None) -> None:
        tele.bot.send_message(self.sender_id, '\U0001f552 - cобираю данные, подождите.')

        messages_batch = ['\U0001F4C6 - СТАТИСТИКА ЗА НЕДЕЛЮ\n\n']

        ...

    @staticmethod
    def build_result_message_general_values_day(data: dict[str, Any]) -> str:
        messages_batch = ['\U0001F4C5 - СТАТИСТИКА ЗА ДЕНЬ']

        for section_name, section_data in data.items():
            section_messages = [f'\n\n{section_name.upper()}\n']

            section_messages.append('\U00002b07\U0000fe0f - Суммарно\n')
            for statistic_item in section_data['total']:
                name, value = statistic_item
                section_messages.append(f'{name.capitalize()}: {value}')

            section_messages.append('\n\U00002b07\U0000fe0f - По сотрудникам')
            for users_statistics in section_data['per_employee']:
                section_messages.append(f'\n{users_statistics["full_name"]}')
                for statistic_item_data in users_statistics['statistics']:
                    item_name, item_value = statistic_item_data
                    section_messages.append(f'\t\t\t{item_name}: {item_value if item_value else "0"}')

            messages_batch.append('\n'.join(section_messages))

        return '\n'.join(messages_batch)

    def send_general_values_day(self, section_id=None) -> None:
        """TODO"""

        tele.bot.send_message(self.sender_id, '\U0001f552 - cобираю данные, подождите.')

        data = get_statistic_for_today(filter_by_section_id=section_id)
        result_message = self.build_result_message_general_values_day(data=data)

        tele.bot.send_message(self.sender_id, result_message, reply_markup=tele.main_markup)

    def send_general_values_accumulative(self, section_id=None) -> None:
        """TODO"""

        tele.bot.send_message(self.sender_id, '\U0001f552 - cобираю данные, подождите.')

        data = get_statistic_accumulate(filter_by_section_id=section_id, accumulative=True)
        # result_message = self.build_result_message_general_values_day(data=data)
        #
        tele.bot.send_message(self.sender_id, result_message, reply_markup=tele.main_markup)

    def send_statistics(self, message: Message) -> None:
        """TODO"""

        tele.bot.send_message(
            self.sender_id,
            text='\U00002b07\U0000fe0f - выберите направление',
            reply_markup=self.statistics_markup,
        )
        tele.bot.register_next_step_handler(message, self._choose_statistics_type)
