from enum import Enum
import copy

from sqlalchemy import and_, or_
from sqlalchemy.orm import relationship, contains_eager

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .user import User


class PositionSortFilter(Enum):
    # Most relevant recommended positions
    RECOMMENDED = 'recommended'

    # Latest active positions
    LATEST = 'latest'

    @classmethod
    def lookup(cls, sort_name):
        if sort_name is None:
            return None

        try:
            return PositionSortFilter(sort_name.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported sorting filter: {sort_name}.") from ex


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
            'apply_url'
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
            'hiring_manager': self.hiring_manager.as_custom_dict(['location', 'phone_number', 'email']),
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
        add_if_not_none('apply_url', self.details.get('apply_url'))
        add_if_not_none('is_bookmarked', self.is_bookmarked if hasattr(self, 'is_bookmarked') else None)

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
    def search(
        cls, tx, user,
        sort=None, keyword=None, department=None, location=None, role=None, role_type=None, pay_grade=None,
        limit=None
    ):  # pylint: disable=too-many-arguments
        positions = tx.query(cls).join(Position.hiring_manager).where(and_(
            User.customer_id == user.customer_id,
            cls.status != PositionStatus.DELETED.value
        ))

        if sort is not None and sort == PositionSortFilter.LATEST:
            positions = positions.order_by(Position.created_at.desc())

        if keyword is not None:
            positions = positions.where(or_(
                Position.role.ilike(f'%{keyword}%'),
                Position.details['description'].astext.ilike(f'%{keyword}%'),  # pylint: disable=unsubscriptable-object
                Position.details['benefits'].astext.ilike(f'%{keyword}%')  # pylint: disable=unsubscriptable-object
            ))

        if department is not None:
            positions = positions.filter(Position.department.ilike(f'%{department}%'))

        if location is not None:
            positions = positions.where(Position.location == location)

        if role is not None:
            positions = positions.filter(Position.role.ilike(f'%{role}%'))

        if role_type is not None:
            positions = positions.where(Position.role_type == role_type)

        # TODO: (santanu) Need to implement pay grade based on customer profile
        if pay_grade is not None:
            positions = positions.filter(
                Position.details['pay_grade'].astext.ilike(f'%{pay_grade}%'))  # pylint: disable=unsubscriptable-object

        if limit is not None:
            positions = positions.limit(int(limit))

        # Transform dataset with is_bookmarked flag
        positions_ = []
        for position in positions:
            position.is_bookmarked = any(bookmark.user_id == user.id for bookmark in position.bookmark_users)
            positions_.append(position)

        return positions_

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
