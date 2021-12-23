from enum import Enum
import copy

from sqlalchemy import and_
from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .user import User


class PositionRoleType():  # pylint: disable=too-few-public-methods
    SUPPORTED_TYPES = [
        'Full Time',
        'Part Time',
    ]

    @classmethod
    def validate_and_return_role_type(cls, role_type):
        if role_type not in cls.SUPPORTED_TYPES:
            raise InvalidArgumentError(f"Unsupported role type: {role_type}")
        return role_type


class PositionStatus(Enum):
    # Position is available for users
    ACTIVE = 'active'

    # Position has been deleted
    DELETED = 'deleted'


class Position(ModelBase):
    __tablename__ = 'position'

    hiring_manager = relationship(User, foreign_keys="[Position.manager_id]")
    location = relationship("Location")
    details = None

    def update_details(self, payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'description',
            'benefits',
        ]

        for field in details_fields:
            if payload.get(field) is not None:
                if payload[field]:
                    details[field] = payload[field]
                elif field in details:
                    del details[field]

        self.details = details

    def as_dict(self):
        position = {
            'position_id': self.id,
            'hiring_manager': self.hiring_manager.as_summary_dict(),
            'location': self.location.as_dict(),
            'role_type': self.role_type,
            'role': self.role,
            'department': self.department,
            'posted_on': self.created_at.isoformat()
        }

        def add_if_not_none(key, value):
            if value is not None:
                position[key] = value

        add_if_not_none('description', self.details.get('description'))
        add_if_not_none('benefits', self.details.get('benefits'))

        if self.pay_range:
            position['pay_minimum'] = self.pay_range.lower
            position['pay_maximum'] = self.pay_range.upper

        return position

    @classmethod
    def validate_pay_range(cls, pay_range):
        if pay_range.lower > pay_range.upper:
            raise InvalidArgumentError(f"Pay minimum '{pay_range.lower}' should be less than pay maximum '{pay_range.upper}'")

        return pay_range

    @classmethod
    def lookup(cls, tx, position_id, must_exist=True):
        position = tx.query(cls).where(and_(
            cls.id == position_id,
            cls.status == PositionStatus.ACTIVE.value
        )).one_or_none()
        if position is None and must_exist:
            raise DoesNotExistError(f"Position '{position_id}' does not exist")
        return position

    @classmethod
    def search(cls, tx, user):  # pylint: disable=too-many-arguments
        positions = tx.query(cls).where(and_(
            User.customer_id == user.customer_id,
            cls.status == PositionStatus.ACTIVE.value
        ))

        return positions
