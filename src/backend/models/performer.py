from enum import Enum

from sqlalchemy import and_
from sqlalchemy.orm import contains_eager, relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from backend.models.application import Application
from .db import ModelBase
from .post import Post
from .user import User


class PerformerStatus(Enum):
    IN_PROGRESS = 'in_progress'
    SUSPENDED = 'suspended'
    STOPPED = 'stopped'
    COMPLETE = 'complete'

    # TODO: (sunil) create an EnumLookupMixin that can be shared by all the Enums
    @classmethod
    def lookup(cls, performer_status):
        if performer_status is None:
            return None

        try:
            return cls(performer_status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid performer status: {performer_status}.") from ex


class Performer(ModelBase):
    __tablename__ = 'performer'

    application = relationship("Application")

    @classmethod
    def lookup_by_post(cls, tx, post_id):
        # TODO: (sunil) We may need to support for filtering by status
        query_options = [
            contains_eager(cls.application).joinedload(Application.post, innerjoin=True),
            contains_eager(cls.application).joinedload(Application.applicant, innerjoin=True)
        ]

        return tx.query(cls).join(cls.application).join(Application.post).where(
            Post.id == post_id).options(query_options).order_by(cls.created_at.desc())

    @classmethod
    def lookup(cls, tx, post_id, performer_id):
        query_options = [
            contains_eager(cls.application).joinedload(Application.post, innerjoin=True),
            contains_eager(cls.application).joinedload(Application.applicant, innerjoin=True)
        ]

        performer = tx.query(cls).join(cls.application).join(Application.post).join(Application.applicant).where(and_(
            Post.id == post_id,
            User.id == performer_id
        )).options(query_options).one_or_none()

        if performer is None:
            raise DoesNotExistError(f"Performer '{performer_id}' does not exist for post '{post_id}'")
        return performer

    def as_dict(self):
        return {
            'post_id': self.application.post.id,
            'user_id': self.application.applicant.id,
            'status': self.status
        }
