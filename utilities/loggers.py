import logging
from kuai_log import get_logger

file_logger = get_logger(name='gwy_exam_file', level=logging.DEBUG, log_filename='gwy_exam.log',
                log_path='./logs', is_add_file_handler=True,
                json_log_path='./logs/json', is_add_json_file_handler=True,
            )