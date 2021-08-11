from sqlalchemy import select
from sqlalchemy.exc import StatementError

from backend.common.exceptions import InvalidArgumentError
from .db import ModelBase


class ProductPreference(ModelBase):
    __tablename__ = 'product_preference'

    @classmethod
    def lookup_multiple(cls, tx, ids, must_exist=True):
        try:
            products = tx.execute(select(cls).where(cls.id.in_(ids))).scalars().all()
        except StatementError as ex:
            # TODO: (sunil) log the original exception
            # This can happen, for example, if the given id is not a valid UUID
            raise InvalidArgumentError("Product preference lookup failed") from ex

        if must_exist:
            # pylint: disable=consider-using-set-comprehension
            unknown_ids = set(ids) - set([product.id for product in products])
            # pylint: enable=consider-using-set-comprehension
            if unknown_ids:
                raise InvalidArgumentError(f"Product preference lookup failed: {', '.join(unknown_ids)}")
        return products

    def as_dict(self):
        return {
            'product_id': self.id,
            'name': self.name,
        }
