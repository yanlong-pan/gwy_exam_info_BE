import logging
from kuai_log import get_logger

debug_file_logger = get_logger(name='debug_file_logger', level=logging.DEBUG, log_filename='debug.log',
                log_path='./logs/debug', is_add_file_handler=True,
                json_log_path='./logs/debug/json', is_add_json_file_handler=True,
            )

error_file_logger = get_logger(name='error_file_logger', level=logging.ERROR, log_filename='error.log',
                log_path='./logs/error', is_add_file_handler=True,
                json_log_path='./logs/error/json', is_add_json_file_handler=True,
            )