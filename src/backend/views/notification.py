from flask import request
from flask_cognito import current_cognito_jwt

from backend.common.exceptions import NotAllowedError
from backend.common.http import make_no_content_response
from backend.models.db import transaction
from backend.models.notification import Notification, NotificationStatus
from backend.models.user import User
from backend.views.base import AuthenticatedAPIBase


class NotificationAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        limit = int(request.args.get('limit')) if request.args.get('limit') is not None else None
        start = int(request.args.get('start')) if request.args.get('start') is not None else None

        user_id = current_cognito_jwt['sub']
        with transaction() as tx:
            notifications = Notification.lookup_multiple(tx, user_id, start=start, limit=limit)
            return {
                'notifications': [notification.as_dict() for notification in notifications],
                'total_unread': Notification.get_unread_count(tx, user_id),
            }


class NotificationByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(notification_id):
        with transaction() as tx:
            notification = Notification.lookup(tx, notification_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            if notification.user_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the notified user")

            notification.status = NotificationStatus.lookup(request.json['status']).value
            return notification.as_dict()

    @staticmethod
    def delete(notification_id):
        with transaction() as tx:
            notification = Notification.lookup(tx, notification_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            if notification.user_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the notified user")

            notification.status = NotificationStatus.DELETED.value
        return make_no_content_response()
