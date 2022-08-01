from enum import Enum
import copy

from sqlalchemy import and_, or_
from sqlalchemy.orm import relationship, contains_eager

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .user import User


class ProjectStatus(Enum):
    # Position is available for users
    ACTIVE = 'active'

    # Position has been deleted
    DELETED = 'deleted'


class Project(ModelBase):
    __tablename__ = 'project'

    client = relationship("ProjectClient")
    manager = relationship(User, foreign_keys="[Project.manager_id]")
    details = None

    def update_details(self, payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'description'
        ]

        for field in details_fields:
            if payload.get(field) is not None:
                if payload[field]:
                    details[field] = payload[field]
                elif field in details:
                    del details[field]

        if payload.get('hashtags') is not None:
            if payload['hashtags']:
                details['hashtags'] = payload['hashtags']
            elif 'hashtags' in details:
                del details['hashtags']

        self.details = details

    def as_dict(self, return_keys=all):
        project = {
            'project_id': self.id,
            'client_id': self.client_id, 
            'manager': self.manager.as_custom_dict(['location', 'phone_number', 'email'])
        }

        def add_if_required(key, value):
            if (return_keys is all or key in return_keys) and value is not None:
                project[key] = value

        add_if_required('description', self.details.get('description'))
        add_if_required('hashtags', self.details.get('hashtags'))
    
        return project

    @classmethod
    def lookup(cls, tx, project_id, user=None, must_exist=True):
        project = tx.query(cls).where(and_(
            cls.id == project_id,
            cls.status == ProjectStatus.ACTIVE.value
        )).one_or_none()
        if project is None and must_exist:
            raise DoesNotExistError(f"Project '{project_id}' does not exist")

        return project

    @classmethod
    def search(
        cls, tx, user, client, keyword
    ):  # pylint: disable=too-many-arguments
        projects = tx.query(cls).join(Project.manager).where(and_(
            User.customer_id == user.customer_id,
            cls.status != ProjectStatus.DELETED.value
        )).order_by(Project.created_at.desc())

        if keyword is not None:
            projects = projects.where(or_(
                Project.name.ilike(f'%{keyword}%'),
                Project.details['description'].astext.ilike(f'%{keyword}%'),  # pylint: disable=unsubscriptable-object
                Project.details['hashtags'].astext.ilike(f'%{keyword}%')
            ))

        if client is not None:
            projects = projects.where(Project.client == client)

        return projects


class ProjectClient(ModelBase):  # pylint: disable=too-few-public-methods
    __tablename__ = 'project_client'

    projects = relationship("projects", back_populates="bookmark_users")

    @classmethod
    def lookup(cls, tx, user_id, position_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, position_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Client for project '{position_id}' and user '{user_id}' does not exist")
        return bookmark
