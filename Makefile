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

first-notify:
	poetry run python notifier.py -c kpi-first

second-notify:
	poetry run python notifier.py -c kpi-second

lawsuits:
	poetry run python notifier.py -c lawsuits

lint:
	poetry run flake8
