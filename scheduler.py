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

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c kpi-first')  # noqa
    notify.setall('0 20 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c kpi-second')  # noqa
    notify.setall('30 20 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c plan-day-first')  # noqa
    notify.setall('5 10 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c plan-day-second')  # noqa
    notify.setall('35 10 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c plan-week-first')  # noqa
    notify.setall('0 10 * * 1')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c plan-week-second')  # noqa
    notify.setall('30 10 * * 1')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c day')  # noqa
    notify.setall('0 21 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c day-law')  # noqa
    notify.setall('2 21 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c day-sales')  # noqa
    notify.setall('4 21 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c week-law')  # noqa
    notify.setall('7 21 * * 5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c week-sales')  # noqa
    notify.setall('8 21 * * 5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c week')  # noqa
    notify.setall('5 21 * * 5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c lawsuits')  # noqa
    notify.setall('0 18 * * 5')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/updater.py -c week-sales')  # noqa
    update.setall('0 22 * * 0')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/updater.py -c week-law')  # noqa
    update.setall('5 22 * * 0')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/updater.py -c day-sales')  # noqa
    update.setall('10 22 * * 1-5')

    cron.write()


if __name__ == '__main__':
    main()
