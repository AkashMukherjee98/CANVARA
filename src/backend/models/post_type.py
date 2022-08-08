from backend.common.exceptions import DoesNotExistError
from .db import ModelBase


class PostType(ModelBase):
    __tablename__ = 'post_type'

    @classmethod
    def lookup(cls, tx, post_type_id, must_exist=True):
        post_type = tx.get(cls, post_type_id)
        if post_type is None and must_exist:
            raise DoesNotExistError(f"Post type '{post_type_id}' does not exist")
        return post_type

    def as_dict(self):
        return {
            'post_type_id': self.id,
            'name': self.name
        }
