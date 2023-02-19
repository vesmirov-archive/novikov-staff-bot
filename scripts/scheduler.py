"""
    Schedules notifications and sheetsupdates
"""

import os
import getpass

from crontab import CronTab

USER = getpass.getuser()


def main():
    """
        Schedule notifications via Crontab
    """

    cron = CronTab(user=USER)
    cron.env['HOME'] = f'/home/{USER}'
    cwd = os.getcwd()

    # notifier
    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c general-motivation')
    update.setall('0 22 * * 1-5')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c personal-motivation')
    update.setall('1 22 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c kpi-first')
    notify.setall('0 20 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c kpi-second')
    notify.setall('30 20 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c plan-day-first')
    notify.setall('5 10 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c plan-day-second')
    notify.setall('35 10 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c plan-week-first')
    notify.setall('0 10 * * 1')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c plan-week-second')
    notify.setall('30 10 * * 1')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c day')
    notify.setall('0 21 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c day-law')
    notify.setall('1 21 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c day-sales')
    notify.setall('2 21 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c day-head')
    notify.setall('3 21 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c week-law')
    notify.setall('7 21 * * 5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c week-sales')
    notify.setall('8 21 * * 5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c week-head')
    notify.setall('9 21 * * 5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c week')
    notify.setall('5 21 * * 5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c lawsuits')
    notify.setall('0 18 * * 5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c income')
    notify.setall('0 21 * * 1-5')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/updater.py -c week-sales')
    update.setall('0 22 * * 0')

    # updater
    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/updater.py -c week-law')
    update.setall('5 22 * * 0')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/updater.py -c day-sales')
    update.setall('10 22 * * 1-5')

    cron.write()


if __name__ == '__main__':
    main()
