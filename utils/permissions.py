

def user_has_permission(func):
    """
    Permission decorator.
    Checks if the telegram user is in DB and has access to the bot.
    Otherwise sends an error message.
    """

    def inner(message):
        if db.user_exists(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, DENY_ANONIMUS_MESSAGE)
    return inner


def user_is_admin(func):
    """
    Permission decorator.
    Checks if the telegram user is admin (DB: "is_admin" field).
    Otherviwe sends an error message.
    """

    def inner(message):
        if db.user_is_admin(cursor, message.from_user.id):
            func(message)
        else:
            bot.send_message(message.from_user.id, DENY_MESSAGE)
    return inner