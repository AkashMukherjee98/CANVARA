from sqlalchemy import select
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import relationship

from common.exceptions import InvalidArgumentError
from .db import db, ModelBase

class ProductPreference(ModelBase):
    __table__ = db.metadata.tables['product_preference']

    @classmethod
    def lookup_multiple(cls, tx, ids, must_exist=True):
        try:
            products = tx.execute(select(cls).where(cls.id.in_(ids))).scalars().all()
        except StatementError:
            # TODO: (sunil) log the original exception
            # This can happen, for example, if the given id is not a valid UUID
            raise InvalidArgumentError("Product preference lookup failed")

        if must_exist:
            unknown_ids = set(ids) - set([product.id for product in products])
            if unknown_ids:
                raise InvalidArgumentError(f"Product preference lookup failed: {', '.join(unknown_ids)}")
        return products

    def as_dict(self):
        return {
            'product_id': self.id,
            'name': self.name,
        }
