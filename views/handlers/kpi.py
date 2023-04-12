from sheets.handlers.statistics import update_employee_kpi, prepare_kpi_keys_and_questions
from settings import settings, telegram as tele


class KPIHandler:
    def __init__(self, sender_id):
        self.sender_id = sender_id

    def _parse_answer(self, message, kpi_keys: list[str]) -> None:
        values_from_user = message.text.split()

        if len(values_from_user) != len(kpi_keys):
            tele.bot.send_message(
                self.sender_id,
                '\U0000274E - количество показателей не соответствует числу вопросов. Попробуйте еще раз.',
            )
            return

        if list(filter(lambda item: not item.isnumeric(), values_from_user)):
            tele.bot.send_message(
                self.sender_id,
                '\U0000274E - неверный формат показателей. Попробуйте еще раз.',
            )
            return

        tele.bot.send_message(self.sender_id, '\U0001f552 - вношу данные.')

        data = list(zip(kpi_keys, values_from_user))
        update_employee_kpi(self.sender_id, data)
        tele.bot.send_message(self.sender_id, '\U00002705 - данные внесены. Хорошего вечера!')
        return

    def receive_kpi(self, message):
        kpi_keys, kpi_questions = prepare_kpi_keys_and_questions(self.sender_id)
        if len(kpi_keys) == 0:
            tele.bot.send_message(
                self.sender_id,
                '\U0001F44C - сегодня у вас не нет запланированных отчетов. Спасибо!',
            )
            return

        questions_str = '\n'.join([f'{order + 1}. {question}' for order, question in enumerate(kpi_questions)])
        text = '\U0001F4CB - пришлите следующие количественные данные одним сообщением, согласно приведенному порядку. ' \
               f'Разделяйте числа пробелами:\n\n{questions_str}',
        tele.bot.send_message(self.sender_id, text)

        tele.bot.register_next_step_handler(message, self._parse_answer, kpi_keys)
