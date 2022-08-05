import copy
from enum import Enum

from sqlalchemy import and_, or_
from sqlalchemy.orm import relationship, noload, contains_eager

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .location import Location
from .user import User
from .user_upload import UserUpload
from .skill import SkillWithLevelMixin
from .project import Project


class AssignmentSortFilter(Enum):
    LATEST = 'latest'
    RECOMMENDED = 'recommended'

    @classmethod
    def lookup(cls, filter_key):
        if filter_key is None:
            return None

        try:
            return AssignmentSortFilter(filter_key.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported sorting option: {filter_key}.") from ex


class AssignmentStatus(Enum):
    ACTIVE = 'active'
    DELETED = 'deleted'


class Assignment(ModelBase):
    __tablename__ = 'assignment'

    creator = relationship(User, foreign_keys="[Assignment.creator_id]")
    project = relationship(Project)
    location = relationship(Location)

    video_description = relationship(UserUpload, foreign_keys="[Assignment.video_description_id]")

    required_skills = relationship("AssignmentSkill")

    bookmark_users = relationship("AssignmentBookmark", back_populates="assignment")
    details = None

    MAX_SKILLS = 50

    def update_details(self, assignment_payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'description'
        ]

        for field in details_fields:
            if assignment_payload.get(field) is not None:
                if assignment_payload[field]:
                    details[field] = assignment_payload[field]
                elif field in details:
                    del details[field]

        if assignment_payload.get('hashtags') is not None:
            if assignment_payload['hashtags']:
                details['hashtags'] = assignment_payload['hashtags']
            elif 'hashtags' in details:
                del details['hashtags']

        self.details = details

    @classmethod
    def validate_skills(cls, skills):
        num_skills_selected = len(skills)

        if num_skills_selected > cls.MAX_SKILLS:
            raise InvalidArgumentError(
                f"Skills selected: {num_skills_selected} You can't select more than {cls.MAX_SKILLS} skills.")

        skill_names_seen = set()
        for skill in skills:
            # Make sure there are no duplicate entries
            name = skill['name'].lower()
            if name in skill_names_seen:
                raise InvalidArgumentError(f"Multiple skill '{skill['name']}' found with same name.")
            skill_names_seen.add(name)

            AssignmentSkill.validate_skill_level(skill['name'], skill.get('level'))

    def set_skills(self, tx, skills):
        AssignmentSkill.update_skills(tx, self.customer_id, self.required_skills, skills)

    def as_dict(self, return_keys=all):  # if return_keys=all return everything, if any key(s) specified then return those only
        assignment = {
            'assignment_id': self.id,
            'name': self.name
        }

        def add_if_required(key, value):
            if (return_keys is all or key in return_keys) and value is not None:
                assignment[key] = value

        add_if_required('creator', self.creator.as_summary_dict())
        add_if_required('project', self.project.as_dict())
        add_if_required('location', self.location.as_dict())

        add_if_required(
            'video_description', self.video_description.as_dict(method='get') if self.video_description else None)

        add_if_required('required_skills', [skill.as_dict() for skill in self.required_skills])

        add_if_required('role', self.role if self.role else None)
        add_if_required('start_date', self.start_date if self.start_date else None)

        add_if_required('description', self.details.get('description'))
        add_if_required('hashtags', self.details.get('hashtags'))

        add_if_required('created_at', self.created_at.isoformat() if self.created_at else None)
        add_if_required('last_updated_at', self.last_updated_at.isoformat() if self.last_updated_at else None)

        add_if_required('is_bookmarked', self.is_bookmarked if hasattr(self, 'is_bookmarked') else None)

        return assignment

    @classmethod
    def lookup(cls, tx, assignment_id, user=None, must_exist=True):
        assignment = tx.query(cls).where(and_(
            cls.id == assignment_id,
            cls.status == AssignmentStatus.ACTIVE.value
        )).one_or_none()
        if assignment is None and must_exist:
            raise DoesNotExistError(f"Assignment '{assignment_id}' does not exist")

        if user is not None:
            # Transform dataset with is_bookmarked flag
            assignment.is_bookmarked = any(bookmark.user_id == user.id for bookmark in assignment.bookmark_users)

        return assignment

    @classmethod
    def search(
        cls, tx, user, sort=None, keyword=None, location=None, limit=None
    ):  # pylint: disable=too-many-arguments, disable=unsubscriptable-object
        assignments = tx.query(cls).where(and_(
            Assignment.customer_id == user.customer_id,
            cls.status == AssignmentStatus.ACTIVE.value
        ))

        if sort is not None and sort == AssignmentSortFilter.LATEST:
            assignments = assignments.order_by(Assignment.created_at.desc())

        if keyword is not None:
            assignments = assignments.where(or_(
                Assignment.name.ilike(f'%{keyword}%'),
                Assignment.role.ilike(f'%{keyword}%'),
                Assignment.details['description'].astext.ilike(f'%{keyword}%'),
                Assignment.details['hashtags'].astext.ilike(f'%{keyword}%')
            ))

        if location is not None:
            assignments = assignments.where(Assignment.location == location)

        if limit is not None:
            assignments = assignments.limit(int(limit))

        query_options = []

        assignments = assignments.options(query_options)

        # Transform dataset with is_bookmarked flag
        assignments_ = []
        for assignment in assignments:
            assignment.is_bookmarked = any(bookmark.user_id == user.id for bookmark in assignment.bookmark_users)
            assignments_.append(assignment)

        return assignments_

    @classmethod
    def my_bookmarks(
        cls, tx, user
    ):
        assignments = tx.query(cls).where(and_(
            cls.status != AssignmentStatus.DELETED.value
        )).join(Assignment.bookmark_users.and_(AssignmentBookmark.user_id == user.id)).\
            order_by(AssignmentBookmark.created_at.desc())

        query_options = [
            noload(Assignment.project),
            contains_eager(Assignment.bookmark_users)
        ]

        assignments = assignments.options(query_options)
        return assignments


class AssignmentSkill(ModelBase, SkillWithLevelMixin):
    __tablename__ = 'assignment_skill'


class AssignmentBookmark(ModelBase):  # pylint: disable=too-few-public-methods
    __tablename__ = 'assignment_bookmark'

    user = relationship("User")
    assignment = relationship("Assignment", back_populates="bookmark_users")

    @classmethod
    def lookup(cls, tx, user_id, assignment_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, assignment_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Bookmark for assignment '{assignment_id}' and user '{user_id}' does not exist")
        return bookmark


class AssignmentApplicationStatus(Enum):
    NEW = 'new'
    ACTIVE_READ = 'active_read'
    SELECTED = 'selected'
    REJECTED = 'rejected'

    DELETED = 'deleted'

    @classmethod
    def lookup(cls, application_status):
        if application_status is None:
            return None

        try:
            return cls(application_status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid application status: {application_status}.") from ex


class AssignmentApplicationFilter(Enum):
    # All applications except deleted
    ALL = 'all'

    # New and active_read applications
    ACTIVE = 'active'

    SELECTED = 'selected'
    REJECTED = 'rejected'

    @classmethod
    def lookup(cls, filter_key):
        if filter_key is None:
            return None

        try:
            return cls(filter_key.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported filter: {filter_key}.") from ex


class AssignmentApplication(ModelBase):
    __tablename__ = 'assignment_application'

    assignment = relationship(Assignment, foreign_keys="[AssignmentApplication.assignment_id]")
    applicant = relationship(User, foreign_keys="[AssignmentApplication.applicant_id]")
    details = None

    def update_details(self, payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'description'
        ]

        for field_term in details_fields:
            if payload.get(field_term) is not None:
                if payload[field_term]:
                    details[field_term] = payload[field_term]
                elif field_term in details:
                    del details[field_term]

        self.details = details

    def as_dict(self):
        application = {
            'application_id': self.id,
            'description': self.details.get('description')
        }

        def add_if_not_none(key, value):
            if value is not None:
                application[key] = value

        add_if_not_none('assignment', self.assignment.as_dict())
        add_if_not_none('applicant', self.applicant.as_custom_dict([
            'title', 'pronoun', 'location', 'department', 'email', 'phone_number', 'slack_teams_messaging_id'
            ]) if self.applicant else None)

        add_if_not_none('status', self.status)
        add_if_not_none('decided_at', self.decided_at.isoformat() if self.decided_at else None)
        add_if_not_none('closed_at', self.closed_at.isoformat() if self.closed_at else None)

        add_if_not_none('created_at', self.created_at.isoformat() if self.created_at else None)
        add_if_not_none('last_updated_at', self.last_updated_at.isoformat() if self.last_updated_at else None)

        return application

    @classmethod
    def lookup(cls, tx, application_id, must_exist=True):
        application = tx.query(cls).where(and_(
            cls.id == application_id,
            cls.status != AssignmentApplicationStatus.DELETED.value
        )).one_or_none()
        if application is None and must_exist:
            raise DoesNotExistError(f"Application '{application_id}' does not exist")
        return application

    @classmethod
    def search(cls, tx, user, assignment_id, application_filter=None):  # pylint: disable=too-many-arguments
        applications = tx.query(cls).where(and_(
            User.customer_id == user.customer_id,
            cls.assignment_id == assignment_id,
            cls.status != AssignmentApplicationStatus.DELETED.value
        ))

        if application_filter == AssignmentApplicationFilter.ACTIVE:
            applications = applications.where(cls.status.in_([
                AssignmentApplicationStatus.NEW.value, AssignmentApplicationStatus.ACTIVE_READ.value]))
        elif application_filter == AssignmentApplicationFilter.SELECTED:
            applications = applications.where(cls.status == AssignmentApplicationStatus.SELECTED.value)
        elif application_filter == AssignmentApplicationFilter.REJECTED:
            applications = applications.where(cls.status == AssignmentApplicationStatus.REJECTED.value)

        query_options = []

        applications = applications.options(query_options)
        return applications
