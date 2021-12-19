import copy
from enum import Enum

from sqlalchemy import and_
from sqlalchemy.orm import joinedload, relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .user import User
from .location import Location
from .user_upload import UserUpload


class EventStatus(Enum):
    # Event is available for users
    ACTIVE = 'active'

    # Event has been deleted
    DELETED = 'deleted'


class Event(ModelBase):
    __tablename__ = 'event'

    primary_organizer = relationship(User, foreign_keys="[Event.primary_organizer_id]")
    secondary_organizer = relationship(User, foreign_keys="[Event.secondary_organizer_id]")
    location = relationship(Location)

    event_logo = relationship(UserUpload, foreign_keys="[Event.logo_id]")
    overview_video = relationship(UserUpload, foreign_keys="[Event.video_overview_id]")
    details = None

    EVENT_NAME_MAX_CHAR_LENGTH = 35

    def update_details(self, payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'overview',
            'external_event_link',
            'volunteer_event',
            'maximum_participants',
            'employee_only',
            'open_for_outsiders',
            'contact_email',
            'contact_phone',
            'contact_messaging',
            'rsvp_required',
            'rsvp_link',
        ]
        for field_key in details_fields:
            if payload.get(field_key) is not None:
                if payload[field_key]:
                    details[field_key] = payload[field_key]
                elif field_key in details:
                    del details[field_key]

        if payload.get('hashtags') is not None:
            if payload['hashtags']:
                details['hashtags'] = payload.get('hashtags')
            elif 'hashtags' in details:
                del details['hashtags']

        self.details = details

    def as_dict(self):
        event = {
            'event_id': self.id,
            'name': self.name,
            'primary_organizer': self.primary_organizer.as_summary_dict(),
            'location': self.location.as_dict(),
            'start_datetime': self.start_datetime.isoformat(),
            'end_datetime': self.end_datetime.isoformat()
        }

        if self.secondary_organizer:
            event['secondary_organizer'] = self.secondary_organizer.as_summary_dict()

        if self.event_logo:
            event['event_logo'] = self.event_logo.as_dict(method='get')

        if self.overview_video:
            event['overview_video'] = self.overview_video.as_dict(method='get')

        def add_if_not_none(key, value):
            if value is not None:
                event[key] = value

        event['overview'] = self.details.get('overview')
        add_if_not_none('external_event_link', self.details.get('external_event_link'))
        add_if_not_none('volunteer_event', self.details.get('volunteer_event'))
        add_if_not_none('maximum_participants', self.details.get('maximum_participants'))
        add_if_not_none('employee_only', self.details.get('employee_only'))
        add_if_not_none('open_for_outsiders', self.details.get('open_for_outsiders'))
        add_if_not_none('hashtags', self.details.get('hashtags'))
        add_if_not_none('contact_email', self.details.get('contact_email'))
        add_if_not_none('contact_phone', self.details.get('contact_phone'))
        add_if_not_none('contact_messaging', self.details.get('contact_messaging'))
        add_if_not_none('rsvp_required', self.details.get('rsvp_required'))
        add_if_not_none('rsvp_link', self.details.get('rsvp_link'))

        return event

    @classmethod
    def lookup(cls, tx, event_id, must_exist=True):
        event = tx.query(cls).where(and_(
            cls.id == event_id,
            cls.status == EventStatus.ACTIVE.value
        )).one_or_none()
        if event is None and must_exist:
            raise DoesNotExistError(f"Event '{event_id}' does not exist")
        return event

    @classmethod
    def search(
        cls, tx, user
    ):  # pylint: disable=too-many-arguments
        events = tx.query(cls).where(and_(
            User.customer_id == user.customer_id,
            cls.status == EventStatus.ACTIVE.value
        ))

        query_options = [
            joinedload(Event.secondary_organizer)
        ]

        events = events.options(query_options)
        return events

    @classmethod
    def validate_event_name(cls, name):
        if len(name) > cls.EVENT_NAME_MAX_CHAR_LENGTH:
            raise InvalidArgumentError(
                f"Event name must not be more than {cls.EVENT_NAME_MAX_CHAR_LENGTH} characters.")

        return name
