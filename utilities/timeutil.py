import os
import re
import requests
import pytz
from datetime import datetime
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
    formatted_date = re.sub(r'年|月', '-', date_str)
    formatted_date = re.sub(r'日', ' ' if len(date_str) > 10 else '', formatted_date)
    return formatted_date

def extract_end_dt_with_regex(text: str) -> (bool, str):
    datetime_pattern = r"(\d{4}.\d{1,2}.?(\d{0,2}.?)?(.?\d{2}:\d{2})?)"
    datetime_matches = re.findall(datetime_pattern, text.replace('至', '-'))
    try:
        if datetime_matches:
            end_time = format_date(datetime_matches[-1][0])
            return (True, end_time)
        else:
            return (False, text)
    except:
        return (False, text)

def extract_end_dt_with_ai(text: str, collect_date_str: str) -> (bool, str):
    params = {
        'appId': os.getenv('UNI_APP_ID'),
        'collectDate': collect_date_str,
        'text': text,
    }
    response = requests.get(os.getenv('UNI_APP_AI_CLOUD_URL'), params=params)
    if response.status_code == 200:
        dt = extract_end_dt_with_regex(response.text)
        return dt
    else:
        return (False, text)

def extract_end_datetime(text: str, collect_date_str: str):
    # len('报名时间：2023年1月2日 14:30') = 20, 正则匹配仅处理最简单的情况
    if len(text) <= 21:
        isSuccess, result = extract_end_dt_with_regex(text)
        if isSuccess:
            return result
        else:
            _, r = extract_end_dt_with_ai(text, collect_date_str)
            return r
    else:
        _, r = extract_end_dt_with_ai(text, collect_date_str)
        return r
