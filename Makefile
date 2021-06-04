start:
	poetry run python bot.py

prepare:
	poetry run python prepare.py

notify:
	poetry run python notifier.py

day:
	poetry run python notifier.py -a true

lint:
	poetry run flake8
