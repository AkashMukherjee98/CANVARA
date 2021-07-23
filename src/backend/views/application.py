from datetime import datetime
import copy
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt

from backend.common.exceptions import NotAllowedError
from backend.models.application import Application
from backend.models.db import transaction
from backend.models.post import Post
from backend.models.user import User
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase


class PostApplicationAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id):
        with transaction() as tx:
            return jsonify(Application.lookup_multiple(tx, post_id=post_id))

    @staticmethod
    def post(post_id):
        with transaction() as tx:
            # Make sure the user and the post exist
            applicant = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)

            payload = request.json
            details = {
                'description': payload['description']
            }

            # TODO: (sunil) Make sure the post is active
            # TODO: (sunil) Make sure there isn't already an application by this post+applicant

            # Generate a unique id for this post
            application_id = str(uuid.uuid4())

            now = datetime.utcnow()
            application = Application(
                id=application_id,
                post_id=post.id,
                user_id=applicant.id,
                created_at=now,
                last_updated_at=now,
                details=details,
                status=Application.Status.NEW.value
            )
            tx.add(application)
            return application.as_dict()


class ApplicationAPI(AuthenticatedAPIBase):
    @staticmethod
    def __list_applications():
        with transaction() as tx:
            return jsonify(Application.lookup_multiple(tx, applicant_id=current_cognito_jwt['sub']))

    @staticmethod
    def __get_application(application_id):
        with transaction() as tx:
            application = Application.lookup(tx, application_id)
            return application.as_dict()

    @staticmethod
    def get(application_id=None):
        if application_id is None:
            return ApplicationAPI.__list_applications()
        return ApplicationAPI.__get_application(application_id)

    @staticmethod
    def put(application_id):
        with transaction() as tx:
            application = Application.lookup(tx, application_id)
            payload = request.json

            # TODO: (sunil) add authorization -
            #   Only the post owner can change status to rejected/shortlisted/selected
            #   Only the manager of the applicant can change status to approved or denied
            #   Only the applicant can update other values

            details = copy.deepcopy(application.details)
            if 'description' in payload:
                details['description'] = payload['description']
            application.details = details

            # TODO: (sunil) enforce correct state transitions
            if 'status' in payload:
                Application.validate_status(payload['status'])
                application.status = payload['status']
            application.last_updated_at = datetime.utcnow()

        with transaction() as tx:
            application = Application.lookup(tx, application_id)
            return application.as_dict()

    @staticmethod
    def delete(application_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            application = Application.lookup(tx, application_id, must_exist=False)

            if application is None:
                # Noop if the application does not exist
                return {}

            # For now, only the applicant is allowed to delete the application
            if application.applicant.id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the applicant")
            tx.delete(application)
        return {}


class ApplicationVideoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(application_id):
        # TODO: (sunil) add validation for accepted content types
        metadata = {
            'resource': 'application',
            'resource_id': application_id,
            'type': 'video',
        }
        return ApplicationVideoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'applications', metadata)


class ApplicationVideoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(application_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            application = Application.lookup(tx, application_id)
            if status == UserUploadStatus.UPLOADED:
                application.description_video = user_upload
                user_upload.status = status.value
            # TODO: (sunil) return an error if this status transition is not supported

        return {
            'status': user_upload.status,
        }
