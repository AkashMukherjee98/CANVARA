from datetime import datetime
import uuid

from flask import request, jsonify
from flask_cognito import current_cognito_jwt

from backend.common.exceptions import InvalidArgumentError, NotAllowedError, DoesNotExistError
from backend.common.http import make_no_content_response
from backend.common.datetime import DateTime
from backend.models.db import transaction
from backend.models.user import User
from backend.models.location import Location
from backend.models.event import Event, EventStatus, EventComment, EventCommentStatus, EventRSVP, EventRSVPStatus
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


class EventCommentAPI(AuthenticatedAPIBase):
    @staticmethod
    def post(event_id):
        payload = request.json
        comment_id = str(uuid.uuid4())
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            event = Event.lookup(tx, event_id)

            if event is None:
                raise DoesNotExistError(f"Event '{event_id}' does not exist.")

            if 'comment' not in payload.keys():
                raise InvalidArgumentError("Field: comment is required.")

            comment = EventComment(
                id=comment_id,
                event=event,
                creator=user,
                comment=payload.get('comment'),
                status=EventCommentStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(comment)

            return {
                'comment_id': comment.id
            }

    @staticmethod
    def put(event_id, comment_id):
        payload = request.json
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            comment = EventComment.lookup(tx, comment_id)

            if comment.creator != user:
                raise DoesNotExistError(f"User '{user.id}' is not the creator of comment '{comment_id}'.")

            if comment.event_id != event_id:
                raise DoesNotExistError(f"Comment '{comment_id}' does not belongs to event '{event_id}'.")

            if 'comment' not in payload.keys():
                raise InvalidArgumentError("Field: comment is required.")

            comment.comment = payload.get('comment')
            comment.last_updated_at = now

            return {
                'comment_id': comment.id
            }

    @staticmethod
    def delete(event_id, comment_id):
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            comment = EventComment.lookup(tx, comment_id)

            if comment.event_id != event_id:
                raise DoesNotExistError(f"Comment '{comment_id}' does not belongs to Event '{event_id}'.")

            if comment.creator != user:
                raise DoesNotExistError(f"User '{user.id}' is not the creator of comment '{comment_id}'.")

            comment.status = EventCommentStatus.DELETED.value
            comment.last_updated_at = now
        return make_no_content_response()


class EventRSVPAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(event_id):
        status = EventRSVPStatus.lookup(request.json['status'])
        now = datetime.utcnow()

        with transaction() as tx:
            guest = User.lookup(tx, current_cognito_jwt['sub'])
            event = Event.lookup(tx, event_id)
            rsvp = EventRSVP.find(
                tx, event.id, guest.id, [
                    EventRSVPStatus.YES.value,
                    EventRSVPStatus.NO.value,
                    EventRSVPStatus.MAYBE.value])

            if rsvp is None:
                rsvp_id = str(uuid.uuid4())
                rsvp = EventRSVP(
                    id=rsvp_id,
                    guest=guest,
                    event=event,
                    status=status.value,
                    created_at=now,
                    last_updated_at=now
                )
                tx.add(rsvp)
            else:
                rsvp.status = status.value
                rsvp.last_updated_at = now

            return {
                'rsvp_id': rsvp.id,
                'status': rsvp.status,
            }

    @staticmethod
    def delete(event_id):
        now = datetime.utcnow()

        with transaction() as tx:
            guest = User.lookup(tx, current_cognito_jwt['sub'])
            event = Event.lookup(tx, event_id)
            rsvp = EventRSVP.find(tx, event.id, guest.id, [
                EventRSVPStatus.YES.value, EventRSVPStatus.NO.value, EventRSVPStatus.MAYBE.value])

            if rsvp is None:
                raise DoesNotExistError(f"User is not provided RSVP for event '{event_id}'")

            rsvp.status = EventRSVPStatus.DELETED.value
            rsvp.last_updated_at = now

        return make_no_content_response()


class EventGalleryAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(event_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            event = Event.lookup(tx, event_id)

            if user.id not in [event.primary_organizer_id, event.secondary_organizer_id]:
                raise NotAllowedError(f"User '{user.id}' is not a organizer of the event '{event.id}'")

        metadata = {
            'resource': 'event',
            'resource_id': event_id,
            'type': 'event_gallery',
        }
        return EventGalleryAPI.create_user_upload(
            user.id, request.json['filename'], request.json['content_type'], 'events', metadata)


class EventGalleryByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(event_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            event = Event.lookup(tx, event_id)

            if user.id not in [event.primary_organizer_id, event.secondary_organizer_id]:
                raise NotAllowedError(f"User '{user.id}' is not a organizer of the event '{event.id}'")

            if status == UserUploadStatus.UPLOADED:
                event.add_event_gallery_media(user_upload)
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

            if user.id not in [event.primary_organizer_id, event.secondary_organizer_id]:
                raise NotAllowedError(f"User '{user.id}' is not a organizer of the event '{event.id}'")

            event.gallery.remove(user_upload)
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()
