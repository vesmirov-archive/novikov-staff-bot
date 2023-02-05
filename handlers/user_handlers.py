from settings import settings


def user_is_registered(user_id: str) -> bool:
    """TODO"""

    if settings.config['employees'].get(user_id):
        return True
    return False


def user_has_admin_permission(user_id: str) -> bool:
    """TODO"""

    return settings.config['employees'][user_id]['admin']


def get_users_list() -> list[tuple[str, str]]:
    """TODO"""

    users = settings.config['employees'].values()
    return [(user["firstname"], user["lastname"]) for user in users]


def get_user_ids() -> list[str]:
    """TODO"""

    return list(settings.config['employees'].keys())
