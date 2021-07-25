start:
	poetry run python bot.py

prepare:
	poetry run python prepare.py

schedule:
	poetry run python scheduler.py

day:
	poetry run python notifier.py -c day

week:
	poetry run python notifier.py -c week

kpi-first-notify:
	poetry run python notifier.py -c kpi-first

kpi-second-notify:
	poetry run python notifier.py -c kpi-second

plan-day-first-notify:
	poetry run python notifier.py -c plan-day-first

plan-day-second-notify:
	poetry run python notifier.py -c plan-day-second

plan-week-first-notify:
	poetry run python notifier.py -c plan-week-first

plan-week-second-notify:
	poetry run python notifier.py -c plan-week-second

lawsuits:
	poetry run python notifier.py -c lawsuits

lint:
	poetry run flake8
