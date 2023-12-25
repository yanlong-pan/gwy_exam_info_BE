import os
import re
import pytz
from datetime import datetime
from typing import Dict, Optional
from utilities import constant

def get_tz():
    return pytz.timezone(os.getenv('TZ', constant.DEFAULT_TZ))

def localize_native_dt(dt: datetime):
    if dt.tzinfo:
        raise Exception(f'The datetime object already has a timezone {dt.tzinfo}')
    else:
        return get_tz().localize(dt)

def local_dt_str_to_utc_ts(dt_str, format = constant.HYPHEN_JOINED_DATE_FORMAT):
    # 调用timestamp()时会自动计算并使用本地时间，此处强制使用环境变量设置的时区
    return localize_native_dt(datetime.strptime(dt_str, format)).timestamp()

def format_date(date_str: str) -> str:
    # 替换年月日为-
    formatted_date = re.sub(r'年|月', '-', date_str)
    formatted_date = re.sub(r'日', '', formatted_date)
    return formatted_date

def extract_dates(text: str) -> Dict[str, Optional[str]]:
    date_pattern = r"(\d{4}.\d{1,2}.?(\d{0,2}.?)?)"
    # date_pattern = r"(\d{4}[-年]\d{1,2}[-月]?(\d{0,2}(日)?)?)"
    dates = re.findall(date_pattern, text.replace('至', '-'))
    dates = [format_date(date[0]) for date in dates]

    end_time = dates[1] if len(dates) > 1 else (dates[0] if dates else None)
    start_time = dates[0] if len(dates) > 1 else None

    return {
        "start_time": start_time,
        "end_time": end_time if end_time else text
    }