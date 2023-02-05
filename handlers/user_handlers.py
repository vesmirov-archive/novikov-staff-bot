from settings import settings


def user_is_registered(user_id):
    """TODO"""

    if settings.config['employees'].get(user_id):
        return True
    return False


def user_has_admin_permission(user_id):
    """TODO"""

    return settings.config['employees'][user_id]['admin']
