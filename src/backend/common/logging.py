from datetime import datetime, timezone
import collections
import functools
import json
import logging
import socket
import string
import time
import traceback
import uuid

from flask import current_app, request
from flask_cognito import current_cognito_jwt


class JsonFormatter(logging.Formatter):
    LOG_FORMAT = '{timestamp} {hostname} {process} {filename} {lineno} {message}'

    def __init__(self):
        super().__init__(fmt=self.LOG_FORMAT, style='{')
        self.__field_names = [field[1] for field in string.Formatter().parse(self._fmt)]

        try:
            self.hostname = socket.gethostname()
        except Exception:  # pylint: disable=broad-except
            self.hostname = 'unknown'

    def format(self, record):
        record.timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        record.hostname = self.hostname

        # allow 'message' to be a dict so we can log arbitrary key-value pairs
        # without having to add them to the log format string
        if isinstance(record.msg, dict):
            record.message = record.msg
        else:
            record.message = record.getMessage()

        log_dict = collections.OrderedDict()
        for field_name in self.__field_names:
            value = getattr(record, field_name)

            # if the value is a dict, unpack it and log every key-value separately
            # typically this should only happen for 'message', but that's not enforced
            if isinstance(value, dict):
                log_dict.update(value)
            else:
                log_dict[field_name] = value
        return json.dumps(log_dict)


def api_trace(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        current_app.logger.info(collections.OrderedDict({
            'request_id': request_id,
            'message': 'API CALLED',
            'method': request.method,
            'path': request.full_path,
            'user': current_cognito_jwt['sub'],
            'remote_addr': request.remote_addr,
        }))

        try:
            return_value = func(*args, **kwargs)
        except Exception:
            duration = round((time.time() - start_time) * 1000, 3)
            current_app.logger.info(collections.OrderedDict({
                'request_id': request_id,
                'message': 'API EXCEPT',
                'duration_ms': duration,
                'stack_trace': traceback.format_exc(),
            }))
            raise

        duration = round((time.time() - start_time) * 1000, 3)
        current_app.logger.info(collections.OrderedDict({
            'request_id': request_id,
            'message': 'API RETURN',
            'duration_ms': duration,
        }))
        return return_value
    return wrapper
