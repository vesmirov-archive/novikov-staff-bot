import os
import getpass

from crontab import CronTab

USER = getpass.getuser()


cron = CronTab(user=USER)
cron.env['HOME'] = os.getcwd()
cron.env['PATH'] = os.getcwd()

notify = cron.new(command='.venv/bin/python notifier.py -c kpi-first')
notify.setall('0 20 * * 1-5')

notify = cron.new(command='.venv/bin/python notifier.py -c kpi-second')
notify.setall('30 20 * * 1-5')

update = cron.new(command='.venv/bin/python updater.py -c day')
update.setall('0 21 * * 1-5')

update = cron.new(command='.venv/bin/python updater.py -c week')
update.setall('5 21 * * 5')

update = cron.new(command='.venv/bin/python updater.py -c lawsuits')
update.setall('0 18 * * 5')

cron.write()
