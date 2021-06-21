from sqlalchemy.orm import relationship
from common.exceptions import DoesNotExistError
from .db import db, ModelBase

class Customer(ModelBase):
    __table__ = db.metadata.tables['customer']

    users = relationship("User", back_populates="customer")

    @classmethod
    def lookup(cls, tx, id, must_exist=True):
        customer = tx.get(cls, id)
        if customer is None and must_exist:
            raise DoesNotExistError(f"Customer '{id}' does not exist")
        return customer

    def as_dict(self):
        return {
            'customer_id': self.id,
            'name': self.name,
        }
