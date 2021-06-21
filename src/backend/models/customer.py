from sqlalchemy.orm import relationship
from backend.common.exceptions import DoesNotExistError
from .db import db, ModelBase

class Customer(ModelBase):
    __table__ = db.metadata.tables['customer']

    users = relationship("User", back_populates="customer")

    @classmethod
    def lookup(cls, tx, customer_id, must_exist=True):
        customer = tx.get(cls, customer_id)
        if customer is None and must_exist:
            raise DoesNotExistError(f"Customer '{customer_id}' does not exist")
        return customer

    def as_dict(self):
        return {
            'customer_id': self.id,
            'name': self.name,
        }
