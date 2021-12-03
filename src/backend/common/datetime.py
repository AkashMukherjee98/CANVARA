from datetime import datetime
from backend.common.exceptions import InvalidArgumentError


class DateTime():
    @classmethod
    def validate_and_convert_isoformat_to_date(cls, date, fieldname):
        # date must be in ISO 8601 format (YYYY-MM-DD)
        try:
            return datetime.fromisoformat(date).date()
        except ValueError as ex:
            raise InvalidArgumentError(f"Unable to parse {fieldname}: {date}") from ex

    @classmethod
    def validate_and_convert_isoformat_to_time(cls, time, fieldname):
        # time must be in ISO 8601 format (hh:mm:ss)
        timeformat = "%H:%M:%S"
        try:
            return datetime.strptime(time, timeformat).time()
        except ValueError as ex:
            raise InvalidArgumentError(f"Unable to parse {fieldname}: {time}") from ex
