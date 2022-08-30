from datetime import datetime
import copy
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.models.slack import send_slack_notification
from backend.common.exceptions import NotAllowedError
from backend.common.http import make_no_content_response
from backend.models.application import Application, ApplicationFilter, ApplicationStatus
from backend.models.db import transaction
from backend.models.notification import Notification
from backend.models.performer import Performer, PerformerStatus
from backend.models.post import Post
from backend.models.user import User
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase

from backend.models.activities import Activity, ActivityGlobal, ActivityType


post_application_blueprint = Blueprint('post_application', __name__, url_prefix='/posts/<post_id>/applications')
blueprint = Blueprint('application', __name__, url_prefix='/applications')


@post_application_blueprint.route('')
class PostApplicationAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id):
        application_filter = ApplicationFilter.lookup(request.args.get('filter'))

        with transaction() as tx:
            return jsonify(Application.lookup_by_post(tx, post_id, application_filter=application_filter))

    @staticmethod
    def post(post_id):
        with transaction() as tx:
            # Make sure the user and the post exist
            applicant = User.lookup(tx, current_cognito_jwt['sub'])
            user = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, user, post_id)

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
                post=post,
                applicant=applicant,
                created_at=now,
                last_updated_at=now,
                details=details,
                status=ApplicationStatus.NEW.value
            )
            tx.add(application)

            # Insert activity details in DB
            tx.add(Activity.add_activity(application.applicant, ActivityType.APPLICATION_SUBMITTED, data={
                'gig': {
                    'post_id': application.post.id,
                    'name': application.post.name
                },
                'application': {
                    'application_id': application.id
                },
                'user': {
                    'user_id': application.post.owner.id,
                    'name': application.post.owner.name,
                    'profile_picture_url': application.post.owner.profile_picture_url
                }
            }))
            tx.add(Activity.add_activity(application.post.owner, ActivityType.APPLICATION_SUBMITTED, data={
                'gig': {
                    'post_id': application.post.id,
                    'name': application.post.name
                },
                'application': {
                    'application_id': application.id
                },
                'user': {
                    'user_id': application.applicant.id,
                    'name': application.applicant.name,
                    'profile_picture_url': application.applicant.profile_picture_url
                }
            }))

            # Generate a notification for the post owner
            tx.add(Notification.create_new_application_notification(application))
            send_slack_notification(applicant, "Application created successfully")
            return application.as_dict()


@blueprint.route('')
class ApplicationAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            return jsonify(Application.lookup_by_user(tx, current_cognito_jwt['sub']))


@blueprint.route('/<application_id>')
class ApplicationByIdAPI(AuthenticatedAPIBase):

    @staticmethod
    def get(application_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            application = Application.lookup(tx, user, application_id)
            return application.as_dict()

    @staticmethod
    def put(application_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            application = Application.lookup(tx, user, application_id)
            payload = request.json
            now = datetime.utcnow()

            # TODO: (sunil) add authorization -
            #   Only the post owner can change status to rejected/active_read/selected
            #   Only the manager of the applicant can change status to approved or denied
            #   Only the applicant can update other values

            details = copy.deepcopy(application.details)
            if 'description' in payload:
                details['description'] = payload['description']
            application.details = details

            # TODO: (sunil) enforce correct state transitions
            if 'status' in payload:
                new_status = ApplicationStatus.lookup(payload['status'])
                application.status = new_status.value

                # If the application has been selected, add a new performer
                if application.status != new_status and new_status == ApplicationStatus.SELECTED:
                    tx.add(Performer(
                        application=application,
                        status=PerformerStatus.IN_PROGRESS.value,
                        created_at=now,
                        last_updated_at=now))

                    # Insert activity details in DB
                    tx.add(Activity.add_activity(application.applicant, ActivityType.GIG_ASSIGNED, data={
                        'gig': {
                            'post_id': application.post.id,
                            'name': application.post.name
                        },
                        'application': {
                            'application_id': application.id
                        },
                        'user': {
                            'user_id': application.post.owner.id,
                            'name': application.post.owner.name,
                            'profile_picture_url': application.post.owner.profile_picture_url
                        }
                    }))
                    tx.add(Activity.add_activity(application.post.owner, ActivityType.GIG_ASSIGNED, data={
                        'gig': {
                            'post_id': application.post.id,
                            'name': application.post.name
                        },
                        'application': {
                            'application_id': application.id
                        },
                        'user': {
                            'user_id': application.applicant.id,
                            'name': application.applicant.name,
                            'profile_picture_url': application.applicant.profile_picture_url
                        }
                    }))
                    tx.add(ActivityGlobal.add_activity(application.post.owner.customer, ActivityType.GIG_ASSIGNED, data={
                        'gig': {
                            'post_id': application.post.id,
                            'name': application.post.name
                        },
                        'application': {
                            'application_id': application.id
                        },
                        'user': {
                            'user_id': application.applicant.id,
                            'name': application.applicant.name,
                            'profile_picture_url': application.applicant.profile_picture_url
                        }
                    }))

                # If the application has been passed
                if application.status != new_status and new_status == ApplicationStatus.PASSED:
                    # Insert activity details in DB
                    tx.add(Activity.add_activity(application.applicant, ActivityType.APPLICATION_REJECTED, data={
                        'gig': {
                            'post_id': application.post.id,
                            'name': application.post.name
                        },
                        'application': {
                            'application_id': application.id
                        },
                        'user': {
                            'user_id': application.post.owner.id,
                            'name': application.post.owner.name,
                            'profile_picture_url': application.post.owner.profile_picture_url
                        }
                    }))
                    tx.add(Activity.add_activity(application.post.owner, ActivityType.APPLICATION_REJECTED, data={
                        'gig': {
                            'post_id': application.post.id,
                            'name': application.post.name
                        },
                        'application': {
                            'application_id': application.id
                        },
                        'user': {
                            'user_id': application.applicant.id,
                            'name': application.applicant.name,
                            'profile_picture_url': application.applicant.profile_picture_url
                        }
                    }))

            application.last_updated_at = now
            return application.as_dict()

    @staticmethod
    def delete(application_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            application = Application.lookup(tx, user, application_id)

            # For now, only the applicant is allowed to delete the application
            if application.applicant.id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the applicant")
            application.status = ApplicationStatus.DELETED.value
        return make_no_content_response()


@blueprint.route('/<application_id>/video')
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


@blueprint.route('/<application_id>/video/<upload_id>')
class ApplicationVideoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(application_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            application = Application.lookup(tx, user, application_id)
            if status == UserUploadStatus.UPLOADED:
                application.description_video = user_upload
                user_upload.status = status.value
            # TODO: (sunil) return an error if this status transition is not supported

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(application_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            application = Application.lookup(tx, user, application_id)

            # For now, only the applicant is allowed to delete the application video
            if application.applicant.id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the applicant")
            application.description_video = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()
