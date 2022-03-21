import copy
from enum import Enum

from sqlalchemy import and_, or_, cast, Boolean
from sqlalchemy.orm import relationship, noload, contains_eager

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
    sponsor_community = relationship("Community")
    event_logo = relationship(UserUpload, foreign_keys="[Event.logo_id]")
    overview_video = relationship(UserUpload, foreign_keys="[Event.video_overview_id]")
    comments = relationship("EventComment", primaryjoin=(
        "and_(EventComment.event_id==Event.id, "
        "EventComment.status == 'active')"))
    rsvp = relationship("EventRSVP", primaryjoin=(
        "and_(EventRSVP.event_id==Event.id, "
        "or_(EventRSVP.status == 'yes', "
        "EventRSVP.status == 'no', "
        "EventRSVP.status == 'maybe'))"))
    gallery = relationship("UserUpload", secondary='event_gallery')
    bookmark_users = relationship("EventBookmark", back_populates="event")
    details = None

    EVENT_NAME_MAX_CHAR_LENGTH = 35
    MAX_EVENT_GALLERY_IMAGE = 50
    MAX_EVENT_GALLERY_VIDEO = 1

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
            'start_datetime': self.start_datetime.isoformat(timespec='milliseconds'),
            'end_datetime': self.end_datetime.isoformat(timespec='milliseconds')
        }

        if self.secondary_organizer:
            event['secondary_organizer'] = self.secondary_organizer.as_summary_dict()

        if self.sponsor_community:
            event['sponsor_community'] = self.sponsor_community.as_summary_dict()

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

        if self.comments:
            event['comments'] = [comment.as_dict() for comment in self.comments]

        if self.rsvp:
            event['rsvp'] = [rsvp.as_dict() for rsvp in self.rsvp]

        gallery = [media.as_dict(method='get') for media in self.gallery if media.is_video()]
        gallery.extend([media.as_dict(method='get') for media in self.gallery if media.is_image()])
        if gallery:
            event['gallery'] = gallery

        return event

    def as_summary_dict(self):
        event = {
            'event_id': self.id,
            'name': self.name
        }

        if self.event_logo:
            event['event_logo'] = self.event_logo.as_dict(method='get')

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
        cls, tx, user,
        keyword=None, location=None, sponsor_community=None, event_date=None,
        volunteers_events_only=None, remote_attendance_support=None,
        limit=None
    ):  # pylint: disable=too-many-arguments
        events = tx.query(cls).join(Event.primary_organizer).where(and_(
            User.customer_id == user.customer_id,
            cls.status == EventStatus.ACTIVE.value
        ))

        # pylint: disable=unsubscriptable-object
        if keyword is not None:
            events = events.where(or_(
                Event.name.ilike(f'%{keyword}%'),
                Event.details['overview'].astext.ilike(f'%{keyword}%'),
                Event.details['hashtags'].astext.ilike(f'%{keyword}%')
            ))

        if location is not None:
            events = events.where(Event.location == location)

        if sponsor_community is not None:
            events = events.where(Event.sponsor_community == sponsor_community)

        if event_date is not None:
            events = events.filter(Event.start_datetime <= event_date).filter(Event.end_datetime >= event_date)

        if volunteers_events_only is not None and volunteers_events_only.lower() in ("true", "yes"):
            events = events.filter(cast(Event.details['volunteer_event'].astext, Boolean).is_(True))

        if remote_attendance_support is not None and remote_attendance_support.lower() in ("true", "yes"):
            events = events.filter(cast(Event.details['open_for_outsiders'].astext, Boolean).is_(True))

        if limit is not None:
            events = events.limit(int(limit))
        # pylint: enable=disable=unsubscriptable-object

        query_options = [
            noload(Event.secondary_organizer),
            noload(Event.sponsor_community),
            noload(Event.comments),
            noload(Event.rsvp),
            noload(Event.gallery)
        ]

        events = events.options(query_options)
        return events

    @classmethod
    def my_bookmarks(
        cls, tx, user
    ):
        events = tx.query(cls).where(and_(
            cls.status != EventStatus.DELETED.value
        )).join(Event.bookmark_users.and_(EventBookmark.user_id == user.id)).\
            order_by(EventBookmark.created_at.desc())

        query_options = [
            noload(Event.secondary_organizer),
            noload(Event.sponsor_community),
            noload(Event.comments),
            noload(Event.rsvp),
            noload(Event.gallery),
            contains_eager(Event.bookmark_users)
        ]

        events = events.options(query_options)
        return events

    def add_event_gallery_media(self, media):
        # Event can have limited number of images and video for gallery
        existing_event_gallery = []
        max_size = -1
        if media.is_video():
            existing_event_gallery = [fact for fact in self.gallery if fact.is_video()]
            max_size = self.MAX_EVENT_GALLERY_VIDEO
        elif media.is_image():
            existing_event_gallery = [fact for fact in self.gallery if fact.is_image()]
            max_size = self.MAX_EVENT_GALLERY_IMAGE
        else:
            raise InvalidArgumentError(f"Invalid event gallery media type: '{media.content_type}'")

        if len(existing_event_gallery) >= max_size:
            sorted_facts = sorted(existing_event_gallery, key=lambda fact: fact.created_at)
            for fact in sorted_facts[:len(sorted_facts) - max_size + 1]:
                self.gallery.remove(fact)
        self.gallery.append(media)

    @classmethod
    def validate_event_name(cls, name):
        if len(name) > cls.EVENT_NAME_MAX_CHAR_LENGTH:
            raise InvalidArgumentError(
                f"Event name must not be more than {cls.EVENT_NAME_MAX_CHAR_LENGTH} characters.")

        return name


class EventCommentStatus(Enum):
    # Event comment is available
    ACTIVE = 'active'

    # Event comment has been deleted
    DELETED = 'deleted'


class EventComment(ModelBase):
    __tablename__ = 'event_comment'

    event = relationship(Event)
    creator = relationship(User)

    @classmethod
    def lookup(cls, tx, comment_id):
        comment = tx.query(cls).where(and_(
            cls.id == comment_id,
            cls.status.in_([EventCommentStatus.ACTIVE.value])
        )).one_or_none()
        if comment is None:
            raise DoesNotExistError(f"Comment '{comment_id}' does not exist or has been deleted.")
        return comment

    def as_dict(self):
        return {
            'comment_id': self.id,
            'creator': self.creator.as_summary_dict(),
            'datetime': self.created_at.isoformat(),
            'comment': self.comment
        }


class EventRSVPStatus(Enum):
    # RSVP status is yes
    YES = 'yes'

    # RSVP status is no
    NO = 'no'

    # RSVP status is maybe
    MAYBE = 'maybe'

    # RSVP status is deleted
    DELETED = 'deleted'

    @classmethod
    def lookup(cls, status):
        try:
            return EventRSVPStatus(status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported status: {status}.") from ex


class EventRSVP(ModelBase):
    __tablename__ = 'event_rsvp'

    event = relationship(Event)
    guest = relationship(User)

    @classmethod
    def lookup(cls, tx, rsvp_id):
        rsvp = tx.query(cls).where(and_(
            cls.id == rsvp_id
        )).one_or_none()
        return rsvp

    @classmethod
    def find(cls, tx, event_id, user_id, status):
        rsvp = tx.query(cls).where(and_(
            cls.event_id == event_id,
            cls.guest_id == user_id,
            cls.status.in_(status)
        )).one_or_none()
        return rsvp

    def as_dict(self):
        return {
            'guest': self.guest.as_summary_dict(),
            'status': self.status,
            'date_time': self.last_updated_at.isoformat()
        }


class EventBookmark(ModelBase):  # pylint: disable=too-few-public-methods
    __tablename__ = 'event_bookmark'

    user = relationship("User")
    event = relationship("Event", back_populates="bookmark_users")

    @classmethod
    def lookup(cls, tx, user_id, event_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, event_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Bookmark for event '{event_id}' and user '{user_id}' does not exist")
        return bookmark
