from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.http import make_no_content_response
from backend.common.exceptions import DoesNotExistError, InvalidArgumentError, NotAllowedError
from backend.models.db import transaction
from backend.models.community import Community, CommunityType, CommunityStatus, CommunitySortFilter
from backend.models.community import CommunityAnnouncement, CommunityAnnouncementStatus
from backend.models.community import CommunityMembership, CommunityMembershipStatus
from backend.models.community import CommunityBookmark
from backend.models.user import User
from backend.models.location import Location
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase

from backend.models.activities import Activity, ActivityGlobal, ActivityType

blueprint = Blueprint('community', __name__, url_prefix='/communities')


@blueprint.route('')
class CommunityAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        sort = CommunitySortFilter.lookup(request.args.get('sort')) if 'sort' in request.args else None
        keyword = request.args.get('keyword', None)
        community_type = CommunityType.validate_and_return_community_type(
            request.args.get('community_type')) if 'community_type' in request.args else None

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            location = Location.lookup(tx, request.args.get('location_id')) if 'location_id' in request.args else None

            communities = Community.search(
                tx,
                user,
                community_type=community_type,
                sort=sort,
                keyword=keyword,
                location=location
            )
            communities = [community.as_dict([
                'primary_moderator', 'location', 'community_logo', 'type', 'hashtags', 'sponsor_events',
                'created_at', 'last_updated_at'
            ]) for community in communities]
        return jsonify(communities)

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
            secondary_moderator = User.lookup(tx, payload['secondary_moderator_id']) \
                if payload.get('secondary_moderator_id') else None
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

            # Insert activity details in DB
            activity_data = {
                'community': {
                    'community_id': community.id,
                    'name': community.name
                },
                'user': {
                    'user_id': primary_moderator.id,
                    'name': primary_moderator.name,
                    'profile_picture_url': primary_moderator.profile_picture_url
                }
            }
            tx.add(Activity.add_activity(primary_moderator, ActivityType.NEW_COMMUNITY_CREATED, data=activity_data))
            tx.add(ActivityGlobal.add_activity(
                primary_moderator.customer, ActivityType.NEW_COMMUNITY_CREATED, data=activity_data))

            community_details = community.as_dict()

        return community_details


@blueprint.route('/<community_id>')
class CommunityByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(community_id):
        with transaction() as tx:
            community = Community.lookup(tx, community_id)
            return community.as_dict()

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


@blueprint.route('/<community_id>/community_logo')
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


@blueprint.route('/<community_id>/community_logo/<upload_id>')
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


@blueprint.route('/<community_id>/overview_video')
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


@blueprint.route('/<community_id>/overview_video/<upload_id>')
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


@blueprint.route('/<community_id>/announcements')
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


@blueprint.route('/<community_id>/announcements/<announcement_id>')
class CommunityAnnouncementByIdAPI(AuthenticatedAPIBase):
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


@blueprint.route('/<community_id>/members')
class CommunityMembershipAPI(AuthenticatedAPIBase):
    @staticmethod
    def post(community_id):
        membership_id = str(uuid.uuid4())
        now = datetime.utcnow()

        with transaction() as tx:
            member = User.lookup(tx, current_cognito_jwt['sub'])
            community = Community.lookup(tx, community_id)
            community_membership = CommunityMembership.find(
                tx, community.id, member.id, [
                    CommunityMembershipStatus.PENDINGAPPROVAL.value,
                    CommunityMembershipStatus.DISAPPROVED.value,
                    CommunityMembershipStatus.ACTIVE.value])

            if (community_membership is not None
                    and community_membership.status == CommunityMembershipStatus.PENDINGAPPROVAL.value):
                raise InvalidArgumentError(f"Membership '{community_membership.id}' is pending for moderator approval.")

            if (community_membership is not None
                    and community_membership.status == CommunityMembershipStatus.DISAPPROVED.value):
                raise InvalidArgumentError(f"Membership '{community_membership.id}' is disapproved by the moderator.")

            if community_membership is not None and community_membership.status == CommunityMembershipStatus.ACTIVE.value:
                raise InvalidArgumentError(f"Membership '{community_membership.id}' is already active for user.")

            community_membership_status = CommunityMembershipStatus.ACTIVE.value
            if community.details['membership_approval_required'] is True:
                community_membership_status = CommunityMembershipStatus.PENDINGAPPROVAL.value

            membership_create = CommunityMembership(
                id=membership_id,
                member=member,
                community=community,
                status=community_membership_status,
                created_at=now,
                last_updated_at=now
            )
            tx.add(membership_create)

            return {
                'membership_id': membership_create.id,
                'status': membership_create.status,
            }

    @staticmethod
    def delete(community_id):
        now = datetime.utcnow()

        with transaction() as tx:
            member = User.lookup(tx, current_cognito_jwt['sub'])
            community = Community.lookup(tx, community_id)
            community_membership = CommunityMembership.find(tx, community.id, member.id, [
                CommunityMembershipStatus.PENDINGAPPROVAL.value, CommunityMembershipStatus.ACTIVE.value])

            if community_membership is None:
                raise DoesNotExistError(f"User is not a member of this community '{community_id}'")

            community_membership.status = CommunityMembershipStatus.DISJOINED.value
            community_membership.last_updated_at = now

        return make_no_content_response()


@blueprint.route('/<community_id>/members/<membership_id>')
class CommunityMembershipByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(community_id, membership_id):
        now = datetime.utcnow()
        status = CommunityMembershipStatus.lookup(request.json['status'])

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            community = Community.lookup(tx, community_id)
            community_membership = CommunityMembership.lookup(tx, membership_id)

            if community_membership is None:
                raise DoesNotExistError(f"Membership ID for Community '{community.id}' is not valid.")

            if user.id not in [community.primary_moderator_id, community.secondary_moderator_id]:
                raise NotAllowedError(f"User '{user.id}' is not a owner or moderator of the community'{community.id}'")

            if status in [CommunityMembershipStatus.DISAPPROVED, CommunityMembershipStatus.ACTIVE]:
                community_membership.status = status.value
                community_membership.last_updated_at = now

        return {
            'status': community_membership.status,
        }


@blueprint.route('/<community_id>/gallery')
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


@blueprint.route('/<community_id>/gallery/<upload_id>')
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


@blueprint.route('/<community_id>/bookmark')
class CommunityBookmarkAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(community_id):
        with transaction() as tx:
            community = Community.lookup(tx, community_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            bookmark = CommunityBookmark.lookup(tx, user.id, community.id, must_exist=False)
            if bookmark is None:
                CommunityBookmark(user=user, community=community, created_at=datetime.utcnow())
        return make_no_content_response()

    @staticmethod
    def delete(community_id):
        with transaction() as tx:
            community = Community.lookup(tx, community_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            bookmark = CommunityBookmark.lookup(tx, user.id, community.id)
            tx.delete(bookmark)
        return make_no_content_response()
