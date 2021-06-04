start:
	poetry run python bot.py

prepare:
	poetry run python prepare.py

notify:
	poetry run python notifier.py

lint:
	poetry run flake8
