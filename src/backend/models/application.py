from enum import Enum
import itertools

from sqlalchemy import and_
from sqlalchemy.orm import joinedload, noload, relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .post import Post
from .user import User
from .user_upload import UserUpload


class ApplicationFilter(Enum):
    # All applicants for a post
    ALL = 'all'

    # Only shortlisted applicants
    SHORTLISTED = 'shortlisted'

    # Only applicants who have been selected
    SELECTED = 'selected'

    # Only applicants who have been passed
    PASSED = 'passed'

    @classmethod
    def lookup(cls, application_filter):
        if application_filter is None:
            return None

        try:
            return cls(application_filter.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported filter: {application_filter}.") from ex


# TODO: (sunil) Update this and use it to define the status column
class ApplicationStatus(Enum):
    NEW = 'new'
    SHORTLISTED = 'shortlisted'
    SELECTED = 'selected'
    PASSED = 'passed'
    DELETED = 'deleted'

    @classmethod
    def lookup(cls, status):
        if status is None:
            return None

        try:
            return cls(status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid application status: {status}.") from ex


class Application(ModelBase):
    __tablename__ = 'application'

    applicant = relationship("User", back_populates="applications")
    post = relationship("Post", back_populates="applications")
    description_video = relationship(UserUpload)

    DEFAULT_FILTER = ApplicationFilter.ALL

    @classmethod
    def lookup(cls, tx, application_id, must_exist=True):
        # TODO: (sunil) eagerload other relationships
        query_options = [
            joinedload(Application.description_video)
        ]

        application = tx.query(cls).where(and_(
            cls.id == application_id,
            cls.status != ApplicationStatus.DELETED.value,
        )).options(query_options).one_or_none()
        if application is None and must_exist:
            raise DoesNotExistError(f"Application '{application_id}' does not exist")
        return application

    @classmethod
    def lookup_by_post(cls, tx, post_id, application_filter=None):
        if application_filter is None:
            application_filter = cls.DEFAULT_FILTER

        applications = tx.query(cls).join(cls.post).where(Post.id == post_id).order_by(cls.created_at.desc())

        if application_filter == ApplicationFilter.SHORTLISTED:
            applications = applications.where(cls.status == ApplicationStatus.SHORTLISTED.value)

        elif application_filter == ApplicationFilter.SELECTED:
            applications = applications.where(cls.status == ApplicationStatus.SELECTED.value)

        elif application_filter == ApplicationFilter.PASSED:
            applications = applications.where(cls.status == ApplicationStatus.PASSED.value)

        else:
            # For the default "all" filter, return all non-deleted applications
            applications = applications.where(cls.status != ApplicationStatus.DELETED.value)

        query_options = [
            noload(Application.description_video)
        ]
        return [application.as_dict() for application in applications.options(query_options)]

    @classmethod
    def lookup_by_user(cls, tx, applicant_id):
        applications = tx.query(cls).join(cls.applicant).where(and_(
            cls.status != ApplicationStatus.DELETED.value,
            User.id == applicant_id,
        ))

        query_options = [
            noload(Application.description_video)
        ]
        return [application.as_dict() for application in applications.options(query_options)]

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
