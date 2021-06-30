from backend.common.exceptions import DoesNotExistError
from .db import db, ModelBase


class Location(ModelBase):
    __table__ = db.metadata.tables['location']

    @classmethod
    def lookup(cls, tx, location_id, must_exist=True):
        location = tx.get(cls, location_id)
        if location is None and must_exist:
            raise DoesNotExistError(f"Location '{location_id}' does not exist")
        return location

    def as_dict(self):
        return {
            'location_id': self.id,
            'name': self.name
        }
