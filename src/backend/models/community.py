import copy
from enum import Enum

from sqlalchemy import and_
from sqlalchemy.orm import relationship, noload

from backend.common.exceptions import DoesNotExistError
from .db import ModelBase
from .location import Location
from .user import User
from .user_upload import UserUpload


class CommunityStatus(Enum):
    # Community is available for users
    ACTIVE = 'active'

    # Community has been deleted
    DELETED = 'deleted'


class Community(ModelBase):
    __tablename__ = 'community'

    owner = relationship(User, foreign_keys="[Community.owner_id]")
    moderator = relationship(User, foreign_keys="[Community.moderator_id]")
    location = relationship(Location)
    community_logo = relationship(UserUpload, foreign_keys="[Community.logo_id]")
    overview_video = relationship(UserUpload, foreign_keys="[Community.video_overview_id]")
    details = None

    def update_details(self, payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'mission',
            'target_audience',
            'activities'
        ]

        for field_name in details_fields:
            if payload.get(field_name) is not None:
                if payload[field_name]:
                    details[field_name] = payload[field_name]
                elif field_name in details:
                    del details[field_name]

        if payload.get('type') is not None:
            if payload['type']:
                details['type'] = payload['type']
            elif 'type' in details:
                del details['type']

        self.update_hashtags(payload, details)
        self.details = details

    @classmethod
    def update_hashtags(cls, payload, details):
        if payload.get('hashtags') is not None:
            if payload['hashtags']:
                details['hashtags'] = payload['hashtags']
            elif 'hashtags' in details:
                del details['hashtags']

    def as_dict(self):
        community = {
            'community_id': self.id,
            'name': self.name,
            'owner': self.owner.as_summary_dict(),
            'location': self.location.as_dict(),
            'language': self.language
        }

        if self.moderator:
            community['moderator'] = self.moderator.as_summary_dict()

        if self.community_logo:
            community['community_logo'] = self.community_logo.as_dict(method='get')

        if self.overview_video:
            community['overview_video'] = self.overview_video.as_dict(method='get')

        def add_if_not_none(key, value):
            if value is not None:
                community[key] = value

        add_if_not_none('type', self.details.get('type'))
        add_if_not_none('mission', self.details.get('mission'))
        add_if_not_none('target_audience', self.details.get('target_audience'))
        add_if_not_none('activities', self.details.get('activities'))
        add_if_not_none('hashtags', self.details.get('hashtags'))

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
            noload(Community.moderator)
        ]

        communities = communities.options(query_options)

        return communities
