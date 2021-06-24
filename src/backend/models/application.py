from enum import Enum

from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
from .post import Post
from .user import User


class Application(ModelBase):
    __table__ = db.metadata.tables['application']

    applicant = relationship("User", back_populates="applications")
    post = relationship("Post", back_populates="applications")

    # TODO: (sunil) Update this and use it to define the status column
    class Status(Enum):
        NEW = 'new'
        APPROVED = 'approved'
        DENIED = 'denied'
        REJECTED = 'rejected'
        SHORTLISTED = 'shortlisted'
        SELECTED = 'selected'

    @classmethod
    def lookup(cls, tx, application_id, must_exist=True):
        application = tx.get(cls, application_id)
        if application is None and must_exist:
            raise DoesNotExistError(f"Application '{application_id}' does not exist")
        return application

    @classmethod
    def lookup_multiple(cls, tx, post_id=None, applicant_id=None):
        applications = tx.query(cls)
        if post_id is not None:
            applications = applications.join(Application.post).where(Post.id == post_id)
        elif applicant_id is not None:
            applications = applications.join(Application.applicant).where(User.id == applicant_id)

        return [application.as_dict() for application in applications]

    @classmethod
    def validate_status(cls, status):
        try:
            _ = Application.Status(status).value
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid application status: {status}") from ex

    def as_dict(self):
        return {
            'application_id': self.id,
            'post_id': self.post_id,
            'applicant_id': self.user_id,
            'description': self.details['description'],
            'status': self.status,
        }
