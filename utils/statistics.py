from typing import Union

from settings import settings


def get_user_disbonus_data(user_id: Union[str, int]) -> dict[str, dict[str, Union[str, int]]]:
    """TODO"""

    return settings.config['employees'][str(user_id)]['bonuses']['dis-bonuses']
