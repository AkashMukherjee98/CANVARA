from datetime import datetime
import uuid

from flask import request, jsonify
from flask_cognito import current_cognito_jwt

from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.common.http import make_no_content_response
from backend.common.datetime import DateTime
from backend.models.db import transaction
from backend.models.user import User
from backend.models.location import Location
from backend.models.event import Event, EventStatus
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase


class EventAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        payload = request.json
        event_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {'name', 'start_datetime', 'end_datetime', 'location_id', 'overview'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Parameter: {', '.join(missing_fields)} is required")

        start_datetime = DateTime.validate_and_convert_isoformat_to_datetime(payload['start_datetime'], 'start_datetime')
        end_datetime = DateTime.validate_and_convert_isoformat_to_datetime(payload['end_datetime'], 'end_datetime')

        with transaction() as tx:
            name = Event.validate_event_name(payload['name'])
            primary_organizer = User.lookup(tx, current_cognito_jwt['sub'])
            secondary_organizer = User.lookup(tx, payload['secondary_organizer_id'])
            location = Location.lookup(tx, payload['location_id'])

            event = Event(
                id=event_id,
                primary_organizer=primary_organizer,
                secondary_organizer=secondary_organizer,
                name=name,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                location=location,
                status=EventStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now,
            )
            tx.add(event)

            event.update_details(payload)

            event_details = event.as_dict()
        return event_details

    @staticmethod
    def put(event_id):
        now = datetime.utcnow()

        with transaction() as tx:
            event = Event.lookup(tx, event_id)

            payload = request.json

            if payload.get('secondary_organizer_id'):
                event.secondary_organizer = User.lookup(tx, payload['secondary_organizer_id'])

            if payload.get('name'):
                event.name = payload['name']

            if payload.get('start_datetime'):
                event.start_datetime = DateTime.validate_and_convert_isoformat_to_datetime(
                    payload['start_datetime'], 'start_datetime')

            if payload.get('end_datetime'):
                event.end_datetime = DateTime.validate_and_convert_isoformat_to_datetime(
                    payload['end_datetime'], 'end_datetime')

            if payload.get('location_id'):
                event.location = Location.lookup(tx, payload['location_id'])

            event.last_updated_at = now
            event.update_details(payload)

        with transaction() as tx:
            event = Event.lookup(tx, event_id)
            event_details = event.as_dict()
        return event_details

    @staticmethod
    def delete(event_id):
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            event = Event.lookup(tx, event_id)

            # For now, only the primary organizer is allowed to delete the event
            if event.primary_organizer_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not a primary organizer of the event.")
            event.status = EventStatus.DELETED.value
            event.last_updated_at = now
        return make_no_content_response()

    @staticmethod
    def get(event_id=None):
        if event_id is None:
            return EventAPI.__list_events()
        return EventAPI.__get_event(event_id)

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
    def __get_event(event_id):
        with transaction() as tx:
            event = Event.lookup(tx, event_id)
            return event.as_dict()


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
