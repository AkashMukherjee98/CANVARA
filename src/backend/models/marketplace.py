from enum import Enum

from backend.common.exceptions import InvalidArgumentError


class MarketplaceSort(Enum):
    RECOMMENDED = 'recommended'
    LATEST = 'latest'

    @classmethod
    def lookup(cls, term):
        if term is None:
            return None

        try:
            return MarketplaceSort(term.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported filter: {term}.") from ex
