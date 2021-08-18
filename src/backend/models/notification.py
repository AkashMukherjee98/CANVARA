from datetime import datetime
import enum
import uuid

from sqlalchemy import and_
from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase


class NotificationStatus(enum.Enum):
    READ = 'read'
    UNREAD = 'unread'
    DELETED = 'deleted'

    @classmethod
    def lookup(cls, status):
        try:
            return cls(status)
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid notification status: {status}") from ex


class NotificationType(enum.Enum):
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    NEW_APPLICATION = 'new_application'
    NEW_MATCH = 'new_match'

    @classmethod
    def lookup(cls, notification_type):
        try:
            return cls(notification_type)
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid notification type: {notification_type}") from ex


class Notification(ModelBase):
    __tablename__ = 'notification'

    user = relationship("User")

    DEFAULT_LIMIT = 20
    MAX_LIMIT = 100
    DEFAULT_START_INDEX = 0

    @classmethod
    def lookup(cls, tx, notification_id):
        notification = tx.query(cls).where(and_(
            cls.id == notification_id,
            cls.status != NotificationStatus.DELETED.value,
        )).one_or_none()
        if notification is None:
            raise DoesNotExistError(f"Notification '{notification_id}' does not exist")
        return notification

    @classmethod
    def lookup_multiple(cls, tx, user_id, start=None, limit=None):
        if start is None:
            start = cls.DEFAULT_START_INDEX

        if limit is None:
            limit = cls.DEFAULT_LIMIT
        limit = min(limit, cls.MAX_LIMIT)

        return tx.query(cls).where(and_(
            cls.user_id == user_id,
            cls.status != NotificationStatus.DELETED.value
        )).order_by(Notification.created_at.desc()).offset(start).limit(limit).all()

    @classmethod
    def create_new_application_notification(cls, application):
        return Notification(
            id=str(uuid.uuid4()),
            user=application.post.owner,
            type=NotificationType.NEW_APPLICATION.value,
            data={
                'post_id': application.post_id,
                'application_id': application.id,
                'user': {
                    'user_id': application.applicant.id,
                    'name': application.applicant.name,
                }
            },
            created_at=datetime.utcnow(),
            status=NotificationStatus.UNREAD.value
        )

    def as_dict(self):
        return {
            'notification_id': self.id,
            'type': self.type,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
        }
