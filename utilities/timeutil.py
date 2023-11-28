from datetime import datetime, timezone, timedelta
import re
from typing import List


def is_date_within_range(date_time: str, start_time: datetime.date, end_time: datetime.date, format: str = "%Y-%m-%d") -> bool:
    """
    Check if the given date is within the specified start and end times.

    Args:
    date_time (str): The date string to check.
    start_time (datetime.date): The start date of the range.
    end_time (datetime.date): The end date of the range.
    format (str): The format of the date strings.

    Returns:
    bool: True if date_time is within the range, False otherwise.
    """
    try:
        date: datetime.date = datetime.strptime(date_time, format).date()
        # start = datetime.strptime(start_time, format)
        # end = datetime.strptime(end_time, format)
        # return start <= date <= end
        return start_time <= date <= end_time
    except ValueError:
        # Handle invalid date format
        print(f"Invalid date format. Please use the specified format. {date_time} {date}")
        return False

def get_current_date_in_timezone(tz_hours_offset=8):
    """
    Get the current date in a specified timezone.

    Args:
    tz_hours_offset (int): The timezone offset in hours. Default is 8 (East Asia).

    Returns:
    datetime.date: The current date in the specified timezone.
    """
    tz = timezone(timedelta(hours=tz_hours_offset))
    current_time = datetime.now(tz)
    return current_time.date()


def extract_max_date(els: List[str], date_pattern=r'\d{4}-\d{2}-\d{2}', date_format='%Y-%m-%d'):
    max_date = None

    for e in els:
        match = re.search(date_pattern, e)
        if match:
            try:
                date = datetime.strptime(match.group(), date_format)
                if not max_date or date > max_date:
                    max_date = date
            except ValueError:
                # 如果日期格式不匹配，则跳过此日期
                pass

    return max_date.date() if max_date else None