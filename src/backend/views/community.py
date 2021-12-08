from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt

from backend.common.http import make_no_content_response
from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.models.db import transaction
from backend.models.community import Community, CommunityStatus
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

        required_fields = {'name', 'location_id', 'language', 'type', 'mission', 'membership_approval'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        with transaction() as tx:
            owner = User.lookup(tx, current_cognito_jwt['sub'])
            moderator = User.lookup(tx, payload['moderator_id'])
            location = Location.lookup(tx, payload['location_id'])

            community = Community(
                id=community_id,
                name=payload.get('name'),
                owner=owner,
                moderator=moderator,
                location=location,
                language=payload.get('language'),
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
        with transaction() as tx:
            community = Community.lookup(tx, community_id)

            payload = request.json

            if payload.get('name'):
                community.name = payload['name']

            if payload.get('Moderator_1'):
                community.Moderator_1 = payload['Moderator_1']

            if payload.get('Moderator_2'):
                community.Moderator_2 = payload['Moderator_2']

            if payload.get('location'):
                location = Location.lookup(tx, payload['location'])
                community.location_id = location.id

            community.update_details(payload)

        # Fetch the community again from the database so the updates made above are reflected in the response
        with transaction() as tx:
            community = Community.lookup(tx, community_id)
            community_details = community.as_dict()
        return community_details

    @staticmethod
    def delete(community_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            community = Community.lookup(tx, community_id)

            # For now, only the post owner is allowed to delete the post
            if community.owner_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the community owner")
            community.status = CommunityStatus.DELETED.value
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
