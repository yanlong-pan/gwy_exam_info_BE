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
    datetime_pattern = r"(\d{4}.\d{1,2}.?(\d{1,2}.?)?(.?\d{1,2}:\d{1,2})?)"
    datetime_matches = re.findall(datetime_pattern, text)
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
        print(f"使用AI服务，原输入为{text}，AI解析后为{dt}") # TODO：改为使用logging
        return dt
    else:
        return (False, text)

def extract_end_datetime(text: str, collect_date_str: str, pattern: str = None):
    # 正则匹配仅处理标准格式的情况
    # len('报名时间：2023年1月2日 14:30') = 20
    # 报名时间：2023年1月2日 14:30
    # 报名时间：2023-10-29 08:00至2023-11-07 18:00
    # 报名时间：2023-10-29至2023-11-07
    # 报名时间：2023-10-29 至 2023-11-07
    # pattern = r"报名时间[：:](\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)(?:\s*至\s*)(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)"
    if not pattern:
        pattern = r"报名时间[：:](\d{4}-\d{1,2}-\d{1,2}(?:\s+\d{1,2}:\d{1,2})?)(?:\s*至\s*)(\d{4}-\d{1,2}-\d{1,2}(?:\s+\d{1,2}:\d{1,2})?)"
    text = text.replace('官方报名入口', '').strip()
    if len(text) <= 21 or re.findall(pattern, text):
        isSuccess, result = extract_end_dt_with_regex(text)
        if isSuccess:
            return result
        else:
            ok, r = extract_end_dt_with_ai(text, collect_date_str)
            return r if ok else None
    else:
        _, r = extract_end_dt_with_ai(text, collect_date_str)
        return r
