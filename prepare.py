"""
    Create database and add first values
"""

import psycopg2
from dotenv import dotenv_values

from service.db import connect_database


def main():
    """
        Create 'employees' table in database and adds user from .env file
    """

    env = dotenv_values('.env')
    connect, cursor = connect_database(env)

    try:
        cursor.execute(
            'CREATE TABLE employees ('
            'user_id BIGINT NOT NULL UNIQUE,'
            'username VARCHAR(100) NOT NULL,'
            'firstname VARCHAR(100) NOT NULL,'
            'lastname VARCHAR(100),'
            'department VARCHAR(100),'
            'position VARCHAR(100),'
            'is_admin BOOL NOT NULL);'
        )
        print('Table "employees" created.')
    except psycopg2.errors.DuplicateTable:
        print('Table "employees" already has been created.')
    else:
        user_id = env.get('TELEGRAM_CHAT_ID')
        username = env.get('TELEGRAM_USERNAME')
        firstname = env.get('FIRSTNAME')
        lastname = env.get('LASTNAME')
        department = env.get('DEPARTMENT')
        position = env.get('POSITION')
        if user_id:
            cursor.execute(
                f"INSERT INTO employees VALUES ({user_id}, '{username}', "
                f"'{firstname}', '{lastname}', '{department}', "
                f"'{position}', True);"
            )

    connect.commit()
    connect.close()


if __name__ == '__main__':
    main()
