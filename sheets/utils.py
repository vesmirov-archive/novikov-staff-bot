from datetime import date

from settings import settings


def get_actual_row_for_section(section: str) -> int:
    """TODO"""

    days_diff = date.today() - date.fromisoformat(settings.config['start_date'])
    row_number = days_diff.days + settings.config['sections'][section]['google']['start_row']

    return row_number


def get_actual_row_for_disbonuses() -> int:
    """TODO"""

    days_diff = date.today() - date.fromisoformat(settings.config['start_date'])
    row_number = days_diff.days + settings.config['google']['dis-bonuses']['start_row']

    return row_number
