from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt

from backend.common.http import make_no_content_response
from backend.common.exceptions import DoesNotExistError, InvalidArgumentError, NotAllowedError
from backend.models.db import transaction
from backend.models.community import Community, CommunityStatus
from backend.models.community import CommunityAnnouncement, CommunityAnnouncementStatus
from backend.models.community import CommunityMembership, CommunityMembershipStatus
from backend.models.user import User
from backend.models.location import Location
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase


class CommunityAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        payload = request.json
        community_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {'name', 'location_id', 'type', 'membership_approval_required', 'mission'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        with transaction() as tx:
            primary_moderator = User.lookup(tx, current_cognito_jwt['sub'])
            secondary_moderator = User.lookup(tx, payload['secondary_moderator_id'])
            location = Location.lookup(tx, payload['location_id'])

            community = Community(
                id=community_id,
                name=payload.get('name'),
                primary_moderator=primary_moderator,
                secondary_moderator=secondary_moderator,
                location=location,
                status=CommunityStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(community)

            community.update_details(payload)
            community_details = community.as_dict()

        return community_details

    @staticmethod
    def put(community_id):
        now = datetime.utcnow()

        with transaction() as tx:
            community = Community.lookup(tx, community_id)

            payload = request.json

            if payload.get('name'):
                community.name = payload['name']

            if payload.get('secondary_moderator_id'):
                community.secondary_moderator = User.lookup(tx, payload['secondary_moderator_id'])

            if payload.get('location_id'):
                community.location = Location.lookup(tx, payload['location_id'])

            community.last_updated_at = now
            community.update_details(payload)

        # Fetch the community again from the database so the updates made above are reflected in the response
        with transaction() as tx:
            community = Community.lookup(tx, community_id)
            community_details = community.as_dict()
        return community_details

    @staticmethod
    def delete(community_id):
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            community = Community.lookup(tx, community_id)

            # For now, only the primary moderator is allowed to delete the community
            if community.primary_moderator_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the community primary moderator")
            community.status = CommunityStatus.DELETED.value
            community.last_updated_at = now
        return make_no_content_response()

    @staticmethod
    def get(community_id=None):
        if community_id is None:
            return CommunityAPI.__list_communities()
        return CommunityAPI.__get_community(community_id)

    @staticmethod
    def __list_communities():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            communities = Community.search(
                tx,
                user
            )
            communities = [community.as_dict() for community in communities]
        return jsonify(communities)

    @staticmethod
    def __get_community(community_id):
        with transaction() as tx:
            community = Community.lookup(tx, community_id)
            return community.as_dict()


class CommunityLogoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(community_id):
        metadata = {
            'resource': 'community',
            'resource_id': community_id,
            'type': 'community_logo',
        }
        return CommunityLogoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'communities', metadata)


class CommunityLogoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(community_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            community = Community.lookup(tx, community_id)
            if status == UserUploadStatus.UPLOADED:
                community.logo_id = user_upload.id
                user_upload.status = status.value

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(community_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            community = Community.lookup(tx, community_id)

            community.logo_id = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()


class CommunityVideoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(community_id):
        metadata = {
            'resource': 'community',
            'resource_id': community_id,
            'type': 'community_video',
        }
        return CommunityVideoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'communities', metadata)


class CommunityVideoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(community_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            community = Community.lookup(tx, community_id)
            if status == UserUploadStatus.UPLOADED:
                community.video_overview_id = user_upload.id
                user_upload.status = status.value

            return {
                'status': user_upload.status,
            }

    @staticmethod
    def delete(community_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            community = Community.lookup(tx, community_id)

            community.video_overview_id = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()


class CommunityAnnouncementAPI(AuthenticatedAPIBase):
    @staticmethod
    def post(community_id):
        payload = request.json
        community_announcement_id = str(uuid.uuid4())
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            community = Community.lookup(tx, community_id)

            if community is None:
                raise DoesNotExistError(f"Community '{community_id}' does not exist.")

            if user not in [community.primary_moderator, community.secondary_moderator]:
                raise NotAllowedError(f"User '{user.id}' is not allowed to add announcement for this community.")

            if 'announcement' not in payload.keys():
                raise InvalidArgumentError("Field: announcement is required.")

            community_announcement = CommunityAnnouncement(
                id=community_announcement_id,
                community=community,
                creator=user,
                announcement=payload.get('announcement'),
                status=CommunityAnnouncementStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(community_announcement)

            return {
                'announcement_id': community_announcement_id,
            }

    @staticmethod
    def put(community_id, announcement_id):
        payload = request.json
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            community_announcement = CommunityAnnouncement.lookup(tx, announcement_id)

            if community_announcement.community_id != community_id:
                raise DoesNotExistError(f"Announcement '{announcement_id}' does not belongs to community '{community_id}'.")

            community = community_announcement.community
            if user not in [community.primary_moderator, community.secondary_moderator]:
                raise NotAllowedError(f"User '{user.id}' is not allowed to update this announcement.")

            if 'announcement' not in payload.keys():
                raise InvalidArgumentError("Field: announcement is required.")

            community_announcement.announcement = payload.get('announcement')
            community_announcement.last_updated_at = now

            return {
                'announcement_id': community_announcement.id,
            }

    @staticmethod
    def delete(community_id, announcement_id):
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            community_announcement = CommunityAnnouncement.lookup(tx, announcement_id)

            if community_announcement.community_id != community_id:
                raise DoesNotExistError(f"Announcement '{announcement_id}' does not belongs to Community '{community_id}'.")

            community = community_announcement.community
            if user not in [community.primary_moderator, community.secondary_moderator]:
                raise NotAllowedError(f"User '{user.id}' is not allowed to delete this announcement.")

            community_announcement.status = CommunityAnnouncementStatus.DELETED.value
            community_announcement.last_updated_at = now
        return make_no_content_response()


class CommunityMembershipAPI(AuthenticatedAPIBase):
    @staticmethod
    def post(community_id):
        membership_id = str(uuid.uuid4())
        now = datetime.utcnow()

        with transaction() as tx:
            member = User.lookup(tx, current_cognito_jwt['sub'])
            community = Community.lookup(tx, community_id)
            community_membership = CommunityMembership.lookup(tx, member.id, community.id)

            if community_membership is not None:
                raise InvalidArgumentError(f"User '{member.id}' is already a member of this community '{community_id}'")

            membership_join = CommunityMembership(
                id=membership_id,
                member=member,
                community=community,
                status=CommunityMembershipStatus.JOINED.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(membership_join)

            return {
                'status': membership_join.status,
            }

    @staticmethod
    def delete(community_id):
        now = datetime.utcnow()

        with transaction() as tx:
            member = User.lookup(tx, current_cognito_jwt['sub'])
            community = Community.lookup(tx, community_id)
            community_membership = CommunityMembership.lookup(tx, member.id, community.id)

            if community_membership is None:
                raise DoesNotExistError(f"User '{member.id}' is not a member of this community '{community_id}'")

            community_membership.status = CommunityMembershipStatus.DISJOINED.value
            community_membership.last_updated_at = now

        return make_no_content_response()


class CommunityGalleryAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(community_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            community = Community.lookup(tx, community_id)

            if user.id not in [community.primary_moderator_id, community.secondary_moderator_id]:
                raise NotAllowedError(f"User '{user.id}' is not a owner or moderator of the community'{community.id}'")

        metadata = {
            'resource': 'community',
            'resource_id': community_id,
            'type': 'community_gallery',
        }
        return CommunityGalleryAPI.create_user_upload(
            user.id, request.json['filename'], request.json['content_type'], 'communities', metadata)


class CommunityGalleryByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(community_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            community = Community.lookup(tx, community_id)

            if user.id not in [community.primary_moderator_id, community.secondary_moderator_id]:
                raise NotAllowedError(f"User '{user.id}' is not a owner or moderator of the community'{community.id}'")

            if status == UserUploadStatus.UPLOADED:
                community.add_gallery_media(user_upload)
                user_upload.status = status.value

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(community_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            community = Community.lookup(tx, community_id)

            if user.id not in [community.primary_moderator_id, community.secondary_moderator_id]:
                raise NotAllowedError(f"User '{user.id}' is not a owner or moderator of the community'{community.id}'")

            community.gallery.remove(user_upload)
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()
