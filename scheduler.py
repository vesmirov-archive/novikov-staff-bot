"""
    Schedules notifications and sheetsupdates
"""

import os
import getpass

from crontab import CronTab

USER = getpass.getuser()


def main():
    """Schedule notifications via Crontab"""

    cron = CronTab(user=USER)
    cron.env['HOME'] = f'/home/{USER}'
    cwd = os.getcwd()

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c kpi-first')  # noqa
    notify.setall('0 20 * * 1-5')

    notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c kpi-second')  # noqa
    notify.setall('30 20 * * 1-5')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c day-law')  # noqa
    update.setall('0 21 * * 1-5')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c day-sales')  # noqa
    update.setall('3 21 * * 1-5')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c week')  # noqa
    update.setall('5 21 * * 5')

    update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c lawsuits')  # noqa
    update.setall('0 18 * * 5')

    cron.write()


if __name__ == '__main__':
    main()
