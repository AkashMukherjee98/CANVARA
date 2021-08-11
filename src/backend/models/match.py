from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError
from .db import ModelBase


class UserPostMatch(ModelBase):
    __tablename__ = 'user_post_match'

    user = relationship("User")
    post = relationship("Post", back_populates="user_matches")

    @classmethod
    def lookup(cls, tx, match_id, must_exist=True):
        match = tx.get(cls, match_id)
        if match is None and must_exist:
            raise DoesNotExistError(f"Match '{match_id}' does not exist")
        return match

    @classmethod
    def lookup_multiple(cls, tx, user_id=None, post_id=None):
        matches = tx.query(cls)
        if user_id is not None:
            matches = matches.where(cls.user_id == user_id)

        if post_id is not None:
            matches = matches.where(cls.post_id == post_id)

        return matches.all()

    def as_dict(self):
        return {
            'match_id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'match_level': self.confidence_level,
        }
