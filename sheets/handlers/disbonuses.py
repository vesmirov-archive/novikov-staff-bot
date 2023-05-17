from logging import getLogger
from typing import Union

from settings import settings
from sheets.tools import get_cell_value, update_cell_value
from sheets.utils import get_actual_row_for_disbonuses

logger = getLogger(__name__)


def update_disbonus_for_user(user_id: str, disbonus_id: str, disbonus_value: Union[int, str]) -> None:
    """TODO"""

    try:
        user_id = str(user_id)
        disbonus_column = settings.config['employees'][user_id]['bonuses']['dis-bonuses'][disbonus_id]['column']

        update_cell_value(
            table_id=settings.config['google']['dis-bonuses']['table'],
            sheet_id=settings.config['google']['dis-bonuses']['sheet'],
            value=str(disbonus_value),
            column=disbonus_column,
            row=str(get_actual_row_for_disbonuses()),
        )
    except KeyError:
        logger.exception(f'user with ID: {user_id} does not have a disbonus with the next id: {disbonus_id}')


def get_user_actual_bonus_value(user_id: str):
    """TODO"""

    user_id = str(user_id)
    user_bonus_value_column = settings.config['employees'][user_id]['bonuses']['bonus-value-column']

    value = get_cell_value(
        table_id=settings.config['google']['dis-bonuses']['table'],
        sheet_id=settings.config['google']['dis-bonuses']['sheet'],
        column=user_bonus_value_column,
        row=str(get_actual_row_for_disbonuses()),
    )

    return str(value)
