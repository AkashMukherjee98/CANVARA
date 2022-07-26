import copy
from enum import Enum

from sqlalchemy import and_, or_
from sqlalchemy.orm import relationship, noload, contains_eager

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .location import Location
from .user import User
from .user_upload import UserUpload


class CommunitySortFilter(Enum):
    # Most relevant recommended communities for the user
    RECOMMENDED = 'recommended'

    # Latest active communities for the user
    LATEST = 'latest'

    @classmethod
    def lookup(cls, filter_type):
        if filter_type is None:
            return None

        try:
            return CommunitySortFilter(filter_type.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported sorting option: {filter_type}.") from ex


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


class Community(ModelBase):
    __tablename__ = 'community'

    primary_moderator = relationship(User, foreign_keys="[Community.primary_moderator_id]")
    secondary_moderator = relationship(User, foreign_keys="[Community.secondary_moderator_id]")
    location = relationship(Location)
    sponsor_events = relationship("Event")
    community_logo = relationship(UserUpload, foreign_keys="[Community.logo_id]")
    overview_video = relationship(UserUpload, foreign_keys="[Community.video_overview_id]")
    announcements = relationship("CommunityAnnouncement", primaryjoin=(
        "and_(CommunityAnnouncement.community_id==Community.id, CommunityAnnouncement.status=='active')"))
    members = relationship("CommunityMembership", primaryjoin=(
        "and_(CommunityMembership.community_id==Community.id, "
        "or_(CommunityMembership.status == 'pendingapproval', "
        "CommunityMembership.status == 'disapproved', "
        "CommunityMembership.status == 'active'))"))
    gallery = relationship("UserUpload", secondary='community_gallery')
    bookmark_users = relationship("CommunityBookmark", back_populates="community")
    details = None

    MAX_GALLERY_IMAGE = 50
    MAX_GALLERY_VIDEO = 1

    def update_details(self, payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'membership_approval_required',
            'mission',
            'target_audience',
            'activities',
            'contact_email',
            'contact_phone',
            'contact_messaging',
            'member_can_create_events',
            'member_can_post_photos',
            'member_can_post_updates'
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

        if payload.get('hashtags') is not None:
            self.update_hashtags(payload, details)

        self.details = details

    @classmethod
    def update_hashtags(cls, payload, details):
        if not isinstance(payload['hashtags'], list):
            raise InvalidArgumentError("Hashtags should be a list of string.")

        if len(payload['hashtags']) > 0:
            details['hashtags'] = payload['hashtags']
        else:
            del details['hashtags']

    def as_dict(self, return_keys=all):  # if return_keys=all return everything, if any key(s) specified then return those only
        community = {
            'community_id': self.id,
            'name': self.name
        }

        def add_if_required(key, value):
            if (return_keys is all or key in return_keys) and value is not None:
                community[key] = value

        add_if_required('primary_moderator', self.primary_moderator.as_summary_dict())

        add_if_required(
            'secondary_moderator', self.secondary_moderator.as_summary_dict() if self.secondary_moderator else None)

        add_if_required('location', self.location.as_dict())

        add_if_required(
            'community_logo', self.community_logo.as_dict(method='get') if self.community_logo else None)

        add_if_required(
            'overview_video', self.overview_video.as_dict(method='get') if self.overview_video else None)

        add_if_required('type', self.details.get('type'))
        add_if_required('mission', self.details.get('mission'))
        add_if_required('target_audience', self.details.get('target_audience'))
        add_if_required('activities', self.details.get('activities'))
        add_if_required('membership_approval_required', self.details.get('membership_approval_required'))
        add_if_required('hashtags', self.details.get('hashtags'))
        add_if_required('contact_email', self.details.get('contact_email'))
        add_if_required('contact_phone', self.details.get('contact_phone'))
        add_if_required('contact_messaging', self.details.get('contact_messaging'))

        add_if_required('member_can_create_events', bool(self.details.get('member_can_create_events')))
        add_if_required('member_can_post_photos', bool(self.details.get('member_can_post_photos')))
        add_if_required('member_can_post_updates', bool(self.details.get('member_can_post_updates')))

        add_if_required(
            'announcements', [announcement.as_dict() for announcement in self.announcements] if self.announcements else None)

        add_if_required(
            'members', [member.as_dict() for member in self.members] if self.members else None)

        gallery = [media.as_dict(method='get') for media in self.gallery if media.is_video()]
        gallery.extend([media.as_dict(method='get') for media in self.gallery if media.is_image()])
        add_if_required('gallery', gallery if gallery else None)

        add_if_required(
            'sponsor_events', [
                sponsor_event.as_summary_dict() for sponsor_event in self.sponsor_events] if self.sponsor_events else None)

        add_if_required('created_at', self.created_at.isoformat() if self.created_at else None)
        add_if_required('last_updated_at', self.last_updated_at.isoformat() if self.last_updated_at else None)

        add_if_required('is_bookmarked', self.is_bookmarked if hasattr(self, 'is_bookmarked') else None)

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
    def search(
        cls, tx, user,
        community_type=None, sort=None, keyword=None, location=None, limit=None
    ):  # pylint: disable=too-many-arguments, disable=unsubscriptable-object
        communities = tx.query(cls).join(Community.primary_moderator).where(and_(
            User.customer_id == user.customer_id,
            Community.primary_moderator_id != user.id,
            Community.secondary_moderator_id != user.id,
            cls.status == CommunityStatus.ACTIVE.value
        )).outerjoin(Community.members.and_(
            CommunityMembership.member_id == user.id)).where(
                CommunityMembership.member_id.is_(None))

        if community_type is not None:
            communities = communities.where(Community.details['type'].astext.ilike(community_type))

        if sort is not None and sort == CommunitySortFilter.LATEST:
            communities = communities.order_by(Community.created_at.desc())

        if keyword is not None:
            communities = communities.where(or_(
                Community.name.ilike(f'%{keyword}%'),
                Community.details['type'].astext.ilike(f'%{keyword}%'),
                Community.details['mission'].astext.ilike(f'%{keyword}%'),
                Community.details['activities'].astext.ilike(f'%{keyword}%'),
                Community.details['target_audience'].astext.ilike(f'%{keyword}%'),
                Community.details['hashtags'].astext.ilike(f'%{keyword}%')
            ))

        if location is not None:
            communities = communities.where(Community.location == location)

        if limit is not None:
            communities = communities.limit(int(limit))

        query_options = [
            noload(Community.secondary_moderator),
            noload(Community.announcements),
            noload(Community.members),
            noload(Community.gallery)
        ]

        communities = communities.options(query_options)

        # Transform dataset with is_bookmarked flag
        communities_ = []
        for community in communities:
            community.is_bookmarked = any(bookmark.user_id == user.id for bookmark in community.bookmark_users)
            communities_.append(community)

        return communities_

    def add_gallery_media(self, media):
        # Community can have limited number of images and video for gallery
        existing_gallery = []
        max_size = -1
        if media.is_video():
            existing_gallery = [fact for fact in self.gallery if fact.is_video()]
            max_size = self.MAX_GALLERY_VIDEO
        elif media.is_image():
            existing_gallery = [fact for fact in self.gallery if fact.is_image()]
            max_size = self.MAX_GALLERY_IMAGE
        else:
            raise InvalidArgumentError(f"Invalid gallery media type: '{media.content_type}'")

        if len(existing_gallery) >= max_size:
            sorted_facts = sorted(existing_gallery, key=lambda fact: fact.created_at)
            for fact in sorted_facts[:len(sorted_facts) - max_size + 1]:
                self.gallery.remove(fact)
        self.gallery.append(media)

    @classmethod
    def my_bookmarks(
        cls, tx, user
    ):
        communities = tx.query(cls).where(and_(
            cls.status != CommunityStatus.DELETED.value
        )).join(Community.bookmark_users.and_(CommunityBookmark.user_id == user.id)).\
            order_by(CommunityBookmark.created_at.desc())

        query_options = [
            noload(Community.secondary_moderator),
            noload(Community.sponsor_events),
            noload(Community.announcements),
            noload(Community.members),
            noload(Community.gallery),
            contains_eager(Community.bookmark_users)
        ]

        communities = communities.options(query_options)
        return communities


class CommunityAnnouncementStatus(Enum):
    # Community announcement is available for community
    ACTIVE = 'active'

    # Community announcement has been deleted
    DELETED = 'deleted'


class CommunityAnnouncement(ModelBase):
    __tablename__ = 'community_announcement'

    community = relationship(Community)
    creator = relationship(User)

    @classmethod
    def lookup(cls, tx, community_announcement_id):
        community_announcement = tx.query(cls).where(and_(
            cls.id == community_announcement_id,
            cls.status == CommunityAnnouncementStatus.ACTIVE.value
        )).one_or_none()
        if community_announcement is None:
            raise DoesNotExistError(f"Announcement '{community_announcement_id}' does not exist or has been deleted.")
        return community_announcement

    def as_dict(self):
        return {
            'announcement_id': self.id,
            'creator': self.creator.as_summary_dict(),
            'date_time': self.created_at.isoformat(),
            'announcement': self.announcement
        }


class CommunityMembershipStatus(Enum):
    # Community membership is pending for approval
    PENDINGAPPROVAL = 'pendingapproval'

    # Community membership is declined by the approver
    DISAPPROVED = 'disapproved'

    # Community member has been active
    ACTIVE = 'active'

    # Community member has been disjoined
    DISJOINED = 'disjoined'

    @classmethod
    def lookup(cls, status):
        try:
            return CommunityMembershipStatus(status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported status: {status}.") from ex


class CommunityMembership(ModelBase):
    __tablename__ = 'community_membership'

    community = relationship(Community)
    member = relationship(User)

    @classmethod
    def lookup(cls, tx, membership_id):
        membership = tx.query(cls).where(and_(
            cls.id == membership_id
        )).one_or_none()
        return membership

    @classmethod
    def find(cls, tx, community_id, user_id, status):
        membership = tx.query(cls).where(and_(
            cls.community_id == community_id,
            cls.member_id == user_id,
            cls.status.in_(status)
        )).one_or_none()
        return membership

    def as_dict(self):
        return {
            'membership_id': self.id,
            'member': self.member.as_summary_dict(),
            'status': self.status,
            'join_date': self.created_at.isoformat()
        }


class CommunityBookmark(ModelBase):  # pylint: disable=too-few-public-methods
    __tablename__ = 'community_bookmark'

    user = relationship("User")
    community = relationship("Community", back_populates="bookmark_users")

    @classmethod
    def lookup(cls, tx, user_id, community_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, community_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Bookmark for community '{community_id}' and user '{user_id}' does not exist")
        return bookmark
