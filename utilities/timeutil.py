from datetime import datetime
import os

import pytz
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