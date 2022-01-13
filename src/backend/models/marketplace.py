from enum import Enum

from backend.common.exceptions import InvalidArgumentError


class MarketplaceSort(Enum):
    RECOMMENDED = 'recommended'
    LATEST = 'latest'

    @classmethod
    def lookup(cls, name):
        if name is None:
            return None

        try:
            return MarketplaceSort(name.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported filter: {name}.") from ex
