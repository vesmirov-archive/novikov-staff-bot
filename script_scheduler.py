"""
    Schedules crontab notifications
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

    # notifier
    cron.new(
        command=f'{cwd}/.venv/bin/python {cwd}/script_notifier.py -a statistics-day',
    ).setall('0 21 * * 1-5')

    # reminder
    cron.new(
        command=f'{cwd}/.venv/bin/python {cwd}/script_notifier.py -a send-kpi-reminder',
    ).setall('0 19 * * 1-5')

    cron.write()


if __name__ == '__main__':
    main()
