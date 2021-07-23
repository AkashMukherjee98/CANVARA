from enum import Enum
import itertools

from sqlalchemy.orm import joinedload, noload, relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
from .post import Post
from .user import User
from .user_upload import UserUpload


class Application(ModelBase):
    __table__ = db.metadata.tables['application']

    applicant = relationship("User", back_populates="applications")
    post = relationship("Post", back_populates="applications")
    description_video = relationship(UserUpload)

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
        query_options = [
            joinedload(Application.description_video)
        ]
        application = tx.get(cls, application_id, options=query_options)
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

        query_options = [
            noload(Application.description_video)
        ]
        return [application.as_dict() for application in applications.options(query_options)]

    @classmethod
    def validate_status(cls, status):
        try:
            _ = Application.Status(status).value
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid application status: {status}") from ex

    def as_dict(self):
        application = {
            'application_id': self.id,
            'post_id': self.post_id,
            'applicant_id': self.user_id,
            'description': self.details['description'],
            'status': self.status,
        }

        if self.description_video:
            application['video_url'] = self.description_video.generate_get_url()

        if self.post and (self.post.required_skills or self.post.desired_skills):
            application['matched_skills'] = []
            application['unmatched_skills'] = []
            for post_skill in itertools.chain(self.post.required_skills, self.post.desired_skills):
                if any(post_skill.matches(user_skill) for user_skill in self.applicant.current_skills):
                    application['matched_skills'].append(post_skill.as_dict())
                else:
                    application['unmatched_skills'].append(post_skill.as_dict())
        return application
