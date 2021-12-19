import copy
from enum import Enum
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import relationship, noload

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .location import Location
from .user import User
from .user_upload import UserUpload


class CommunityStatus(Enum):
    # Community is available for users
    ACTIVE = 'active'

    # Community has been deleted
    DELETED = 'deleted'


class CommunityType():  # pylint: disable=too-few-public-methods
    SUPPORTED_TYPES = [
        'Engineering',
        'Sports',
        'Social Activities'
    ]

    @classmethod
    def validate_and_return_community_type(cls, communty_type):
        if communty_type not in cls.SUPPORTED_TYPES:
            raise InvalidArgumentError(f"Unsupported community type: {communty_type}")
        return communty_type


class Announcements:  # pylint: disable=too-few-public-methods
    def __init__(self, text):
        self.date = datetime.utcnow().date().isoformat()
        self.text = text

    def as_dict(self):
        return {
            'date': self.date,
            'announcement': self.text
        }


class Community(ModelBase):
    __tablename__ = 'community'

    primary_moderator = relationship(User, foreign_keys="[Community.primary_moderator_id]")
    secondary_moderator = relationship(User, foreign_keys="[Community.secondary_moderator_id]")
    location = relationship(Location)
    community_logo = relationship(UserUpload, foreign_keys="[Community.logo_id]")
    overview_video = relationship(UserUpload, foreign_keys="[Community.video_overview_id]")
    details = None

    def update_details(self, payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'membership_approval_required',
            'mission',
            'target_audience',
            'activities',
            'contact_email',
            'contact_phone',
            'contact_messaging'
        ]

        for field_name in details_fields:
            if payload.get(field_name) is not None:
                if payload[field_name]:
                    details[field_name] = payload[field_name]
                elif field_name in details:
                    del details[field_name]

        if payload.get('type') is not None:
            if payload['type']:
                details['type'] = CommunityType.validate_and_return_community_type(payload['type'])
            elif 'type' in details:
                del details['type']

        if payload.get('announcements') is not None:
            self.update_announcements(payload, details)

        if payload.get('hashtags') is not None:
            self.update_hashtags(payload, details)

        self.details = details

    @classmethod
    def update_announcements(cls, payload, details):
        if not isinstance(payload['announcements'], list):
            raise InvalidArgumentError("Announcements should be a list of text.")

        if len(payload['announcements']) > 0:
            announcements = []
            if 'announcements' in details:
                announcements = details['announcements']

            for announcement in payload['announcements']:
                announcements.append(Announcements(announcement).as_dict())
            details['announcements'] = announcements
        else:
            del details['announcements']

    @classmethod
    def update_hashtags(cls, payload, details):
        if not isinstance(payload['hashtags'], list):
            raise InvalidArgumentError("Hashtags should be a list of string.")

        if len(payload['hashtags']) > 0:
            details['hashtags'] = payload['hashtags']
        else:
            del details['hashtags']

    def as_dict(self):
        community = {
            'community_id': self.id,
            'name': self.name,
            'primary_moderator': self.primary_moderator.as_summary_dict(),
            'location': self.location.as_dict()
        }

        if self.secondary_moderator:
            community['secondary_moderator'] = self.secondary_moderator.as_summary_dict()

        if self.community_logo:
            community['community_logo'] = self.community_logo.as_dict(method='get')

        if self.overview_video:
            community['overview_video'] = self.overview_video.as_dict(method='get')

        def add_if_not_none(key, value):
            if value is not None:
                community[key] = value

        community['type'] = self.details.get('type')
        community['mission'] = self.details.get('mission')
        add_if_not_none('target_audience', self.details.get('target_audience'))
        add_if_not_none('activities', self.details.get('activities'))
        add_if_not_none('announcements', self.details.get('announcements'))
        community['membership_approval_required'] = self.details.get('membership_approval_required')
        add_if_not_none('hashtags', self.details.get('hashtags'))
        add_if_not_none('contact_email', self.details.get('contact_email'))
        add_if_not_none('contact_phone', self.details.get('contact_phone'))
        add_if_not_none('contact_messaging', self.details.get('contact_messaging'))

        return community

    @classmethod
    def lookup(cls, tx, community_id, must_exist=True):
        community = tx.query(cls).where(and_(
            cls.id == community_id,
            cls.status == CommunityStatus.ACTIVE.value
        )).one_or_none()
        if community is None and must_exist:
            raise DoesNotExistError(f"Community '{community_id}' does not exist")
        return community

    @classmethod
    def search(cls, tx, user):  # pylint: disable=too-many-arguments
        communities = tx.query(cls).where(and_(
            User.customer_id == user.customer_id,
            cls.status == CommunityStatus.ACTIVE.value
        ))

        query_options = [
            noload(Community.secondary_moderator)
        ]

        communities = communities.options(query_options)

        return communities
