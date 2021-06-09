import os
import getpass

from crontab import CronTab

USER = getpass.getuser()


cron = CronTab(user=USER)
cron.env['PATH'] = f'/home/{USER}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'  # noqa

cwd = os.getcwd()

notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c kpi-first')  # noqa
notify.setall('0 20 * * 1-5')

notify = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/notifier.py -c kpi-second')  # noqa
notify.setall('30 20 * * 1-5')

update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/updater.py -c day')  # noqa
update.setall('0 21 * * 1-5')

update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/updater.py -c week')  # noqa
update.setall('5 21 * * 5')

update = cron.new(command=f'{cwd}/.venv/bin/python {cwd}/updater.py -c lawsuits')  # noqa
update.setall('0 18 * * 5')

cron.write()
