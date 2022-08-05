from enum import Enum

from sqlalchemy import and_
from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError

from .db import ModelBase
from .client import Client


class ProjectStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

    @classmethod
    def lookup(cls, project_status):
        if project_status is None:
            return None

        try:
            return ProjectStatus(project_status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported status : {project_status}.") from ex


class ProjectStatusFilter(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    ALL = 'all'

    @classmethod
    def lookup(cls, filter_term):
        if filter_term is None:
            return None

        try:
            return ProjectStatusFilter(filter_term.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported project status filter: {filter_term}.") from ex


class Project(ModelBase):
    __tablename__ = 'project'

    client = relationship(Client)
    details = None

    def as_dict(self, return_keys=all):  # if return_keys=all return everything, if any key(s) specified then return those only
        project = {
            'project_id': self.id,
            'name': self.name
        }

        def add_if_required(key, value):
            if (return_keys is all or key in return_keys) and value is not None:
                project[key] = value

        add_if_required('client', self.client.as_dict() if self.client else None)

        add_if_required('status', self.status)

        return project

    @classmethod
    def lookup(cls, tx, project_id):
        project = tx.query(cls).where(and_(
            cls.id == project_id
        ))

        project = project.one_or_none()
        if project is None:
            raise DoesNotExistError(f"Client '{project_id}' does not exist")

        return project

    @classmethod
    def search(cls, tx, customer_id, client=None, status=None):
        projects = tx.query(cls).where(and_(
            cls.customer_id == customer_id
        ))

        if client is not None:
            projects = projects.where(and_(
                Project.client_id == client.id
            ))

        if status == ProjectStatusFilter.ACTIVE:
            projects = projects.where(and_(
                Project.status == ProjectStatus.ACTIVE.value
            ))
        elif status == ProjectStatusFilter.INACTIVE:
            projects = projects.where(and_(
                Project.status == ProjectStatus.INACTIVE.value
            ))

        return projects
