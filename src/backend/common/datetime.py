from datetime import datetime
from backend.common.exceptions import InvalidArgumentError


class DateTime():  # pylint: disable=too-few-public-methods
    @classmethod
    def validate_and_convert_isoformat_to_datetime(cls, datetime_iso, fieldname):
        # datetime must be in ISO 8601 format
        timeformat = "%Y-%m-%dT%H:%M:%S.%f%z"
        try:
            return datetime.strptime(datetime_iso, timeformat)
        except ValueError as ex:
            raise InvalidArgumentError(f"Unable to parse {fieldname}: {datetime_iso}") from ex
