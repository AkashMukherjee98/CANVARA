import copy
from sqlalchemy import and_
from sqlalchemy.orm import joinedload, relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .user import User
from .user_upload import UserUpload


class Event(ModelBase):
    __tablename__ = 'event'

    event_organizers = relationship('User', primaryjoin='User.id == any_(foreign(Event.organizers))', uselist=True)

    event_logo = relationship(UserUpload, foreign_keys="[Event.logo_id]")
    overview_video = relationship(UserUpload, foreign_keys="[Event.overview_video_id]")
    details = None

    EVENT_NAME_MAX_CHAR_LENGTH = 35

    @classmethod
    def lookup(cls, tx, event_id, must_exist=True):
        event = tx.query(cls).where(and_(
            cls.id == event_id
        )).one_or_none()
        if event is None and must_exist:
            raise DoesNotExistError(f"Event '{event_id}' does not exist")
        return event

    @classmethod
    def search(
        cls, tx, user
    ):  # pylint: disable=too-many-arguments
        events = tx.query(cls).where(and_(
            User.customer_id == user.customer_id
        ))

        query_options = [
            joinedload(Event.event_organizers)
        ]

        events = events.options(query_options)
        return events

    def as_dict(self):
        event = {
            'event_id': self.id,
            'name': self.name,
            'location': self.location,
            'language': self.language,
            'overview': self.overview,
            'event_date': self.event_date.isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }

        if self.event_organizers:
            event['organizers'] = [organizer.as_summary_dict() for organizer in self.event_organizers]

        if self.event_logo:
            event['event_logo'] = self.event_logo.as_dict(method='get')

        if self.overview_video:
            event['overview_video'] = self.overview_video.as_dict(method='get')

        def add_if_not_none(key, value):
            if value is not None:
                event[key] = value

        add_if_not_none('volunteer_event', self.details.get('volunteer_event'))
        add_if_not_none('event_link', self.details.get('event_link'))
        add_if_not_none('people_needed', self.details.get('people_needed'))
        add_if_not_none('employee_only', self.details.get('employee_only'))
        add_if_not_none('open_for_outsiders', self.details.get('open_for_outsiders'))
        add_if_not_none('hashtags', self.details.get('hashtags'))
        add_if_not_none('contact_email', self.details.get('contact_email'))
        add_if_not_none('contact_phone', self.details.get('contact_phone'))
        add_if_not_none('contact_messaging', self.details.get('contact_messaging'))
        add_if_not_none('rsvp_required', self.details.get('rsvp_required'))
        add_if_not_none('rsvp_link', self.details.get('rsvp_link'))

        return event

    def update_details(self, payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'volunteer_event',
            'event_link',
            'people_needed',
            'employee_only',
            'open_for_outsiders',
            'hashtags',
            'contact_email',
            'contact_phone',
            'contact_messaging',
            'rsvp_required',
            'rsvp_link',
        ]
        for field_name in details_fields:
            if payload.get(field_name) is not None:
                if payload[field_name]:
                    details[field_name] = payload[field_name]
                elif field_name in details:
                    del details[field_name]

        if payload.get('hashtags') is not None:
            if payload['hashtags']:
                details['hashtags'] = payload.get('hashtags')
            elif 'hashtags' in details:
                del details['hashtags']

        self.details = details

    @classmethod
    def validate_event_name(cls, name):
        if len(name) > cls.EVENT_NAME_MAX_CHAR_LENGTH:
            raise DoesNotExistError(
                f"Event name '{name}' Should not be more than {cls.EVENT_NAME_MAX_CHAR_LENGTH} characters.")

        return name

    @classmethod
    def validate_and_return_organizers(cls, tx, user_id, organizers):
        if len(set(organizers)) < len(organizers):
            raise InvalidArgumentError("Duplicate organizer found in organizers.")

        if user_id in organizers:
            raise InvalidArgumentError(
                f"Loggedin user {user_id} is default organizer hence not required in organizers.")

        organizer_list = [user_id]
        for organizer in organizers:
            try:
                User.lookup(tx, organizer)
                organizer_list.append(organizer)
            except Exception as ex:
                raise InvalidArgumentError(
                    f"Orginzer is not a valid user: {organizer}.") from ex

        return organizer_list
