import os
import getpass

from crontab import CronTab

USER = getpass.getuser()


cron = CronTab(user=USER)
cron.env['HOME'] = os.getcwd()
cron.env['PATH'] = os.getcwd()

notify = cron.new(command='.venv/bin/python notifier.py')
notify.setall('0 20 * * 1-5')

update = cron.new(command='.venv/bin/python updater.py -a true')
update.setall('0 21 * * 1-5')

cron.write()
