"""
    Notifies users through a specific way (flags):
    '-c day' -- send day statistic
    '-c week' -- send week statistic
    '-c kpi-first' -- send first kpi notification
    '-c kpi-second' -- send second kpi notification
    '-c plan-day-first' -- send first day plan notification
    '-c plan-day-second' -- send second day plan notification
    '-c plan-week-first' -- send first week plan notification
    '-c plan-week-second' -- send second week plan notification
    '-c lawsuits' -- send lawsuits notification
"""

import argparse
import json

from dotenv import dotenv_values
import pygsheets
import telebot

import messages
from service import db
from service import spredsheet

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', dest='config')
args = parser.parse_args()

env = dotenv_values('.env')

with open('config.json', 'r') as file:
    CONFIG = json.loads(file.read())

TOKEN = env.get('TELEGRAM_STAFF_TOKEN')

CLIENT_SECRET_FILE = env.get('CLIENT_SECRET_FILE')


def remind_to_send_kpi(bot, manager, second=False):
    """
        Notifications abount sending KPI values
    """

    text = messages.KPI_SECOND_MESSAGE if second else messages.KPI_MESSAGE

    departments_tracked = []
    for department, positions in CONFIG['отслеживание'].items():
        tracked = list(filter(lambda x: x, positions.values()))
        if tracked:
            departments_tracked.append(department)

    for department in departments_tracked:
        needed_employees = spredsheet.check_employees_values_for_fullness(
            manager,
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets'][department],
            department
        )
        for employee_id in needed_employees:
            bot.send_message(employee_id, text)


def remind_to_send_plan(bot, manager, period, second=False):

    if period == 'день':
        text = messages.DAY_PLAN_SECOND_MESSAGE if second else messages.DAY_PLAN_MESSAGE
    else:
        text = messages.WEEK_PLAN_SECOND_MESSAGE if second else messages.WEEK_PLAN_MESSAGE

    departments_tracked = []
    for department, positions in CONFIG['отслеживание'].items():
        tracked = list(filter(lambda x: x, positions.values()))
        if tracked:
            departments_tracked.append(department)

    for department in departments_tracked:
        needed_employees = spredsheet.check_employees_plan_for_fullness(
            manager,
            CONFIG['google']['tables']['план']['table'],
            CONFIG['google']['tables']['план']['sheets'][department],
            department,
            period
        )
        for employee_id in needed_employees:
            bot.send_message(employee_id, text)


def send_daily_results(bot, manager):
    """
        Sends daily results
    """

    departments_tracked = []
    for department, positions in CONFIG['отслеживание'].items():
        tracked = list(filter(lambda x: x, positions.values()))
        if tracked:
            departments_tracked.append(department)

    departments_statistic = []
    for department in departments_tracked:
        day = spredsheet.get_daily_detail_statistic(
            manager,
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets'][department],
            department
        )
        departments_statistic.append(day)

    department_leaders = {}
    for department in departments_tracked:
        leaders = spredsheet.get_leaders_from_google_sheet(
            manager,
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets'][department],
            department
        )
        department_leaders.update({department: leaders})

    for recipient_id in CONFIG['рассылка'].values():
        bot.send_message(recipient_id, 'Итоги дня \U0001f4ca')

        for values in departments_statistic:
            result = []
            for position, employees in values.items():
                employees_result = []
                for employee, values in employees.items():
                    employees_result.append(f'\n\U0001F464 {employee}:\n')
                    employees_result.append(
                        '\n'.join([f'{k}: {v}' for k, v in values.items()]))
                result.append(f'\n\n\U0001F53D {position.upper()}')
                result.append('\n'.join(employees_result))
            bot.send_message(recipient_id, '\n'.join(result))

        bot.send_message(recipient_id, 'Красавчики дня \U0001F3C6')

        leaders = []
        for department, values in department_leaders.items():
            if department == 'делопроизводство':
                if values:
                    leaders.append(
                        f'\U0001f38a {department.capitalize()}: ' +
                        ', '.join(values)
                    )
                else:
                    leaders.append(
                        f'\U0001f5ff {department.capitalize()}: ' +
                        'Красавчиков дня нет'
                    )
        bot.send_message(recipient_id, '\n\n'.join(leaders))


def send_weekly_results(bot, manager):
    """
        Sends weekly results
    """

    departments_tracked = []
    for department, positions in CONFIG['отслеживание'].items():
        tracked = list(filter(lambda x: x, positions.values()))
        if tracked:
            departments_tracked.append(department)

    departments_statistic = []
    for department in departments_tracked:
        week = spredsheet.get_weekly_statistic(
            manager,
            CONFIG['google']['tables']['KPI']['table'],
            CONFIG['google']['tables']['KPI']['sheets'][department],
            department
        )
        departments_statistic.append(week)

    for recipient_id in CONFIG['рассылка'].values():
        bot.send_message(recipient_id, 'Итоги недели \U0001f5d3')
        for values in departments_statistic:
            result = []
            result.extend([f'{k}: {v}' for k, v in values.items()])
            bot.send_message(recipient_id, '\n'.join(result))


def send_department_daily_results(bot, manager, cursor, department):
    """
        Send department daily results to employees
    """

    ids = db.return_ids_of_users_from(cursor, department)

    kpi_daily = spredsheet.get_daily_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department
    )

    result = ['Статистика за день \U0001f4c6\n']
    result.extend([f'{k}: {v}' for k, v in kpi_daily.items()])

    for id in ids:
        bot.send_message(id, '\n'.join(result))

    result = ['Статистика по сотрудникам \U0001F465\n']

    kpi_daily_detail = spredsheet.get_daily_detail_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department
    )
    for position, employees in kpi_daily_detail.items():
        employees_result = []
        if employees:
            for employee, values in employees.items():
                employees_result.append(f'\n\U0001F464 {employee}:\n')
                employees_result.append(
                    '\n'.join([f'{k}: {v}' for k, v in values.items()]))
            result.append(f'\n\n\U0001F53D {position.upper()}')
            result.append('\n'.join(employees_result))

    for id in ids:
        bot.send_message(id, '\n'.join(result))


def send_department_weekly_results(bot, manager, cursor, department):
    """
        Send department daily results to employees
    """

    ids = db.return_ids_of_users_from(cursor, department)

    kpi_daily = spredsheet.get_weekly_statistic(
        manager,
        CONFIG['google']['tables']['KPI']['table'],
        CONFIG['google']['tables']['KPI']['sheets'][department],
        department
    )

    result = ['Статистика за неделю \U0001f5d3\n']
    result.extend([f'{k}: {v}' for k, v in kpi_daily.items()])

    for id in ids:
        bot.send_message(id, '\n'.join(result))


def remind_to_send_lawsuits(bot):
    """
        Notifications abont sending lawsuits
    """

    ids = map(str, CONFIG['иски'].values())

    connect, cursor = db.connect_database(env)
    cursor.execute(
        "SELECT user_id FROM employees "
        f"WHERE user_id IN ({', '.join(ids)})"
    )
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]
        bot.send_message(user_id, messages.LAWSUITS_MESSAGE)


def remind_to_send_income(bot):
    """
        Notifications abont sending income
    """

    ids = map(str, CONFIG['выручка'].values())

    connect, cursor = db.connect_database(env)
    cursor.execute(
        "SELECT user_id FROM employees "
        f"WHERE user_id IN ({', '.join(ids)})"
    )
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]
        bot.send_message(user_id, messages.INCOME_MESSAGE)


def send_general_motivation(bot, manager, cursor):
    ids = db.return_users_ids(cursor)

    data = spredsheet.get_general_motivation(
        manager,
        CONFIG['google']['tables']['мотивация']['table'],
        CONFIG['google']['tables']['мотивация']['sheets']['показатели'],
    )

    msg = f"""
КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ

ВЫРУЧКА 💰
    За сегодня -> [факт] {data['выручка']['за сегодня']['факт']}
    За неделю -> [факт] {data['выручка']['за неделю']['факт']} : {data['выручка']['за неделю']['план']} [план]
    За месяц -> [факт] {data['выручка']['за месяц']['факт']} : {data['выручка']['за месяц']['план']} [план]
    За год -> [факт] {data['выручка']['за год']['факт']} : {data['выручка']['за год']['план']} [план]

ИСКИ 🏛
    За сегодня -> [факт] {data['иски']['за сегодня']['факт']}
    За неделю -> [факт] {data['иски']['за неделю']['факт']} : {data['иски']['за неделю']['план']} [план]
    За месяц -> [факт] {data['иски']['за месяц']['факт']} : {data['иски']['за месяц']['план']} [план]
    За год -> [факт] {data['иски']['за год']['факт']} : {data['иски']['за год']['план']} [план]

СДЕЛКИ 🤝
    За сегодня -> [факт] {data['сделки']['за сегодня']['факт']}
    За неделю -> [факт] {data['сделки']['за неделю']['факт']} : {data['сделки']['за неделю']['план']} [план]
    За месяц -> [факт] {data['сделки']['за месяц']['факт']} : {data['сделки']['за месяц']['план']} [план]
    За год -> [факт] {data['сделки']['за год']['факт']} : {data['сделки']['за год']['план']} [план]
    """

    for user_id in ids:
        bot.send_message(
            user_id,
            text=msg,
        )


def send_personal_motivation(bot, manager, cursor):
    ids = db.return_users_ids(cursor)

    data = spredsheet.get_personal_motivation(
        manager,
        CONFIG['google']['tables']['мотивация']['table'],
        CONFIG['google']['tables']['мотивация']['sheets']['показатели'],
    )

    msg = f"""
КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ ПО СОТРУДНИКАМ

(сегодня / неделя / месяц / год)

ЗАСЕДАНИЙ 💼
    Денис Качармин:
        {data['заседаний']['Денис К']['сегодня']} / {data['заседаний']['Денис К']['неделя']} / {data['заседаний']['Денис К']['месяц']} / {data['заседаний']['Денис К']['год']}

    Денис Паршенцев:
        {data['заседаний']['Денис П']['сегодня']} / {data['заседаний']['Денис П']['неделя']} / {data['заседаний']['Денис П']['месяц']} / {data['заседаний']['Денис П']['год']}

    Анна Андреева:
        {data['заседаний']['Анна']['сегодня']} / {data['заседаний']['Анна']['неделя']} / {data['заседаний']['Анна']['месяц']} / {data['заседаний']['Анна']['год']}

    Мария Уварова:
        {data['заседаний']['Мария']['сегодня']} / {data['заседаний']['Мария']['неделя']} / {data['заседаний']['Мария']['месяц']} / {data['заседаний']['Мария']['год']}

РЕШЕНИЙ ✅
    Денис Качармин:
        {data['решений']['Денис К']['сегодня']} / {data['решений']['Денис К']['неделя']} / {data['решений']['Денис К']['месяц']} / {data['решений']['Денис К']['год']}

    Денис Паршенцев:
        {data['решений']['Денис П']['сегодня']} / {data['решений']['Денис П']['неделя']} / {data['решений']['Денис П']['месяц']} / {data['решений']['Денис П']['год']}

    Анна Андреева:
        {data['решений']['Анна']['сегодня']} / {data['решений']['Анна']['неделя']} / {data['решений']['Анна']['месяц']} / {data['решений']['Анна']['год']}

    Мария Уварова:
        {data['решений']['Мария']['сегодня']} / {data['решений']['Мария']['неделя']} / {data['решений']['Мария']['месяц']} / {data['решений']['Мария']['год']}

ИСКОВ 📄
    Денис Качармин:
        {data['исков']['Денис К']['сегодня']} / {data['исков']['Денис К']['неделя']} / {data['исков']['Денис К']['месяц']} / {data['исков']['Денис К']['год']}

    Денис Паршенцев:
        {data['исков']['Денис П']['сегодня']} / {data['исков']['Денис П']['неделя']} / {data['исков']['Денис П']['месяц']} / {data['исков']['Денис П']['год']}

    Анна Андреева:
        {data['исков']['Анна']['сегодня']} / {data['исков']['Анна']['неделя']} / {data['исков']['Анна']['месяц']} / {data['исков']['Анна']['год']}

ИНЫХ ДОКУМЕНТОВ 🗂
    Денис Качармин:
        {data['иных документов']['Денис К']['сегодня']} / {data['иных документов']['Денис К']['неделя']} / {data['иных документов']['Денис К']['месяц']} / {data['иных документов']['Денис К']['год']}

    Денис Паршенцев:
        {data['иных документов']['Денис П']['сегодня']} / {data['иных документов']['Денис П']['неделя']} / {data['иных документов']['Денис П']['месяц']} / {data['иных документов']['Денис П']['год']}

    Анна Андреева:
        {data['иных документов']['Анна']['сегодня']} / {data['иных документов']['Анна']['неделя']} / {data['иных документов']['Анна']['месяц']} / {data['иных документов']['Анна']['год']}

    Мария Уварова:
        {data['иных документов']['Мария']['сегодня']} / {data['иных документов']['Мария']['неделя']} / {data['иных документов']['Мария']['месяц']} / {data['иных документов']['Мария']['год']}

ЛИСТОВ ПОЛУЧЕНО 📥
    Мария Уварова:
        {data['листов получено']['Мария']['сегодня']} / {data['листов получено']['Мария']['неделя']} / {data['листов получено']['Мария']['месяц']} / {data['листов получено']['Мария']['год']}

ЛИСТОВ ПОДАНО 📤
    Мария Уварова:
        {data['листов подано']['Мария']['сегодня']} / {data['листов подано']['Мария']['неделя']} / {data['листов подано']['Мария']['месяц']} / {data['листов подано']['Мария']['год']}
    """  # noqa

    for user_id in ids:
        bot.send_message(
            user_id,
            text=msg,
        )


def main():
    """
        Notification manager
    """

    bot = telebot.TeleBot(TOKEN)
    manager = pygsheets.authorize(service_account_file=CLIENT_SECRET_FILE)
    connect, cursor = db.connect_database(env)

    if args.config == 'day':
        send_daily_results(bot, manager)
    elif args.config == 'day-law':
        send_department_daily_results(bot, manager, cursor, 'делопроизводство')
    elif args.config == 'day-sales':
        send_department_daily_results(bot, manager, cursor, 'продажи')
    elif args.config == 'week':
        send_weekly_results(bot, manager)
    elif args.config == 'week-law':
        send_department_weekly_results(bot, manager, cursor, 'делопроизводство')
    elif args.config == 'week-sales':
        send_department_weekly_results(bot, manager, cursor, 'продажи')
    elif args.config == 'week-head':
        send_department_weekly_results(bot, manager, cursor, 'руководство')
    elif args.config == 'kpi-first':
        remind_to_send_kpi(bot, manager)
    elif args.config == 'kpi-second':
        remind_to_send_kpi(bot, manager, True)
    elif args.config == 'plan-day-first':
        remind_to_send_plan(bot, manager, 'день')
    elif args.config == 'plan-day-second':
        remind_to_send_plan(bot, manager, 'день', True)
    elif args.config == 'plan-week-first':
        remind_to_send_plan(bot, manager, 'неделя')
    elif args.config == 'plan-week-second':
        remind_to_send_plan(bot, manager, 'неделя', True)
    elif args.config == 'lawsuits':
        remind_to_send_lawsuits(bot)
    elif args.config == 'income':
        remind_to_send_income(bot)
    elif args.config == 'general-motivation':
        send_general_motivation(bot, manager, cursor)
    elif args.config == 'personal-motivation':
        send_personal_motivation(bot, manager, cursor)

    connect.close()


if __name__ == '__main__':
    main()
