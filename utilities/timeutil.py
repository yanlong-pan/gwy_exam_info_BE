from datetime import datetime
import os
import re
from typing import List

import pytz
from utilities import constant

def get_tz():
    return pytz.timezone(os.getenv('TZ', constant.DEFAULT_TZ))