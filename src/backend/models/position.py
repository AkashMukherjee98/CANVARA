from enum import Enum
import copy

from sqlalchemy import and_
from sqlalchemy.orm import relationship, contains_eager

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
    bookmark_users = relationship("PositionBookmark", back_populates="position")
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

        position['pay_currency'] = self.pay_currency
        position['pay_minimum'] = float(self.pay_minimum)
        position['pay_maximum'] = float(self.pay_maximum)

        return position

    @classmethod
    def validate_pay_range(cls, pay_currency, pay_minimum, pay_maximum):
        if pay_currency is not None and len(pay_currency) != 3:
            raise InvalidArgumentError(f"Pay currency '{pay_currency}' should be 3 letter currency code")
        if pay_minimum is not None and not isinstance(pay_minimum, (int, float)):
            raise InvalidArgumentError(f"Pay minimum {pay_minimum} should be currency value")
        if pay_maximum is not None and not isinstance(pay_maximum, (int, float)):
            raise InvalidArgumentError(f"Pay maximum {pay_maximum} should be currency value")
        if pay_minimum is not None and pay_maximum is not None and pay_minimum > pay_maximum:
            raise InvalidArgumentError(f"Pay minimum {pay_minimum} should be less than pay maximum {pay_maximum}")
        if (pay_minimum is not None or pay_maximum is not None) and pay_currency is None:
            raise InvalidArgumentError("Pay currency is required if pay minimum or pay maximum is provided")

        return True

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
    def search(cls, tx, user, limit=None):  # pylint: disable=too-many-arguments
        if limit is not None:
            positions = tx.query(cls).where(and_(
                User.customer_id == user.customer_id,
                cls.status == PositionStatus.ACTIVE.value
            )).limit(limit)
        else:
            positions = tx.query(cls).where(and_(
                User.customer_id == user.customer_id,
                cls.status == PositionStatus.ACTIVE.value
            ))

        return positions

    @classmethod
    def my_bookmarks(
        cls, tx, user
    ):
        positions = tx.query(cls).where(and_(
            cls.status != PositionStatus.DELETED.value
        )).join(Position.bookmark_users.and_(PositionBookmark.user_id == user.id)).\
            order_by(PositionBookmark.created_at.desc())

        query_options = [
            contains_eager(Position.bookmark_users)
        ]

        positions = positions.options(query_options)
        return positions


class PositionBookmark(ModelBase):  # pylint: disable=too-few-public-methods
    __tablename__ = 'position_bookmark'

    user = relationship("User")
    position = relationship("Position", back_populates="bookmark_users")

    @classmethod
    def lookup(cls, tx, user_id, position_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, position_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Bookmark for position '{position_id}' and user '{user_id}' does not exist")
        return bookmark
