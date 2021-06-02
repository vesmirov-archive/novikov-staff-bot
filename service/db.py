import psycopg2


def connect_database(env):
    """Connect to database"""

    connect = psycopg2.connect(
        database=env.get('POSTGRES_DB'),
        user=env.get('POSTGRES_USER'),
        password=env.get('POSTGRES_PASSWORD'),
        host=env.get('POSTGRES_HOST'),
        port=env.get('POSTRGES_PORT')
    )
    cursor = connect.cursor()
    return (connect, cursor)


def user_has_permissions(cursor, user_id):
    """Check if given id saved in databse"""

    cursor.execute("SELECT user_id FROM employees")
    rows = cursor.fetchall()
    for row in rows:
        if user_id in row:
            return True
    return False


def user_is_admin_check(cursor, user_id):
    """Check if given id saved in databse"""

    cursor.execute(
        f"SELECT user_id, is_admin FROM employees WHERE user_id = {user_id}")
    rows = cursor.fetchall()
    for row in rows:
        if row[1]:
            return True
    return False


def list_users(cursor):
    """Show list of users"""

    cursor.execute(
        'SELECT username, firstname, lastname, position, is_admin '
        'FROM employees')
    rows = cursor.fetchall()
    users = []
    for row in rows:
        role = '(admin)' if row[4] else ''
        users.append(f'user: {row[1]} {row[2]} [{row[3]}] - {row[0]} {role}')
    return '\n'.join(users)


def add_user(cursor, connect, user_id, username,
            firstname, lastname, position, is_admin):
    """Add user"""

    cursor.execute(
        f"INSERT INTO employees VALUES ({user_id}, '{username}', "
        f"'{firstname}', '{lastname}', '{position}', {is_admin});"
    )
    connect.commit()


def get_employee_position(cursor, user_id):
    cursor.execute(
        f"SELECT position FROM employees WHERE user_id = {user_id}")
    rows = cursor.fetchall()
    position = rows[0][0]
    return position
