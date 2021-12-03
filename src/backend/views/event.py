from datetime import datetime
import uuid

from flask import request, jsonify
from flask_cognito import current_cognito_jwt

from backend.common.http import make_no_content_response
from backend.common.datetime import DateTime
from backend.models.db import transaction
from backend.models.user import User
from backend.models.language import Language
from backend.models.event import Event
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase


class EventAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        payload = request.json
        event_id = str(uuid.uuid4())
        now = datetime.utcnow()

        event_date = DateTime.validate_and_convert_isoformat_to_date(payload['event_date'], 'event_date')
        start_time = DateTime.validate_and_convert_isoformat_to_time(payload['start_time'], 'start_time')
        end_time = DateTime.validate_and_convert_isoformat_to_time(payload['end_time'], 'end_time')

        language = Language.validate_and_convert_language(payload['language'])

        with transaction() as tx:
            name = Event.validate_event_name(payload['name'])
            organizers = Event.validate_and_return_organizers(
                tx, current_cognito_jwt['sub'], payload['organizers'] if 'organizers' in payload else [])

            event = Event(
                id=event_id,
                organizers=organizers,
                name=name,
                event_date=event_date,
                start_time=start_time,
                end_time=end_time,
                location=payload['location'],
                language=language,
                overview=payload['overview'],
                status='active',
                created_at=now,
                last_updated_at=now,
            )
            tx.add(event)

            event_details = event.as_dict()
        return event_details

    @staticmethod
    def __list_events():
        with transaction() as tx:
            # This is the user making the request, for authorization purposes
            user = User.lookup(tx, current_cognito_jwt['sub'])
            events = Event.search(
                tx,
                user
            )
            events = [event.as_dict() for event in events]
        return jsonify(events)

    @staticmethod
    def get():
        return EventAPI.__list_events()


class EventLogoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(event_id):
        metadata = {
            'resource': 'event',
            'resource_id': event_id,
            'type': 'event_logo',
        }
        return EventLogoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'events', metadata)


class EventLogoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(event_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            event = Event.lookup(tx, event_id)
            if status == UserUploadStatus.UPLOADED:
                event.event_logo = user_upload
                user_upload.status = status.value

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(event_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            event = Event.lookup(tx, event_id)

            event.event_logo = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()


class EventVideoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(event_id):
        metadata = {
            'resource': 'event',
            'resource_id': event_id,
            'type': 'event_video',
        }
        return EventVideoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'events', metadata)


class EventVideoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(event_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            event = Event.lookup(tx, event_id)
            if status == UserUploadStatus.UPLOADED:
                event.overview_video = user_upload
                user_upload.status = status.value

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(event_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            event = Event.lookup(tx, event_id)

            event.overview_video = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()
