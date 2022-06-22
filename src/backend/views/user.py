from datetime import datetime

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from sqlalchemy import select

from backend.common.exceptions import NotAllowedError
from backend.common.http import make_no_content_response
from backend.models.db import transaction
from backend.models.language import Language
from backend.models.skill import Skill
from backend.models.user import User, UserTypeFilter, SkillType, UserBookmark
from backend.views.base import AuthenticatedAPIBase
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.models.notification import Notification

blueprint = Blueprint('user', __name__, url_prefix='/users')
customer_user_blueprint = Blueprint('customer_user', __name__, url_prefix='/customers/<customer_id>/users')


@customer_user_blueprint.route('')
class CustomerUserAPI(AuthenticatedAPIBase):

    @staticmethod
    def get(customer_id):
        with transaction() as tx:
            users = tx.execute(select(User).where(User.customer_id == customer_id)).scalars().all()
            user_details = jsonify([user.as_dict() for user in users])
        return user_details

    @staticmethod
    def post(customer_id):
        payload = request.json

        user = User(
            id=payload['user_id'],
            customer_id=customer_id,
            username=payload.get('username'),
            name=payload['name'],
        )
        with transaction() as tx:
            tx.add(user)
            user.update_profile(payload)

            if payload.get('manager_id'):
                user.manager = user.validate_manager(User.lookup(tx, payload['manager_id']))

            if payload.get('current_skills'):
                User.validate_skills(payload['current_skills'], SkillType.CURRENT_SKILL)
                user.set_current_skills(tx, payload['current_skills'])

            if payload.get('desired_skills'):
                User.validate_skills(payload['desired_skills'], SkillType.DESIRED_SKILL)
                user.set_desired_skills(tx, payload['desired_skills'])

            user_details = user.as_dict()
        return user_details


@blueprint.route('')
class UsersAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        user_type = UserTypeFilter.lookup(request.args.get('user_type')) if 'user_type' in request.args else None

        keyword = request.args.get('keyword') if 'keyword' in request.args else None
        title = request.args.get('title') if 'title' in request.args else None
        department = request.args.get('department') if 'department' in request.args else None
        location = request.args.get('location') if 'location' in request.args else None
        language = Language.validate_and_convert_language(
            request.args.get('language')) if 'language' in request.args else None

        tenure_gte = request.args.get('tenure_gte') if 'tenure_gte' in request.args else None
        tenure_lte = request.args.get('tenure_lte') if 'tenure_lte' in request.args else None

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            skill = Skill.lookup(tx, user.customer_id,
                                 request.args.get('skill_id')) if 'skill_id' in request.args else None

            users = User.search(
                tx,
                user,
                user_type=user_type,
                keyword=keyword,
                title=title,
                department=department,
                skill=skill,
                location=location,
                language=language,
                tenure_gte=tenure_gte,
                tenure_lte=tenure_lte
            )
            users = [user.as_custom_dict([
                'title', 'pronoun', 'department', 'location',
                'expert_skills',
                'introduction', 'introduction_video', 'hashtags',
                'email', 'phone_number', 'linkedin_url', 'slack_teams_messaging_id',
                'mentorship_offered', 'mentorship_description', 'mentorship_hashtags',
                'matching_reason'
            ]) for user in users]
        return jsonify(users)


@blueprint.route('/me')
class UserAPI(AuthenticatedAPIBase):

    @staticmethod
    def get():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_details = user.as_dict()
            user_details['customer_name'] = user.customer.name
            user_details['profile_completion'] = User.profile_completion(user)
            user_details['unread_notifications'] = Notification.get_unread_count(tx, user.id)
        return user_details


@blueprint.route('/<user_id>')
class UserByIdAPI(AuthenticatedAPIBase):

    @staticmethod
    def get(user_id):
        with transaction() as tx:
            user = User.lookup(tx, user_id)

            # If the user is viewing someone else's profile,
            # remove concerns and additional_comments from the feedback
            scrub_feedback = current_cognito_jwt['sub'] != user_id
            user_details = user.as_dict(scrub_feedback=scrub_feedback)
            user_details['customer_name'] = user.customer.name
        return user_details

    @staticmethod
    def put(user_id):
        with transaction() as tx:
            user = User.lookup(tx, user_id)

            payload = request.json

            if payload.get('name'):
                user.name = payload['name']

            if payload.get('username'):
                user.username = payload['username']

            if payload.get('manager_id'):
                manager = User.lookup(tx, payload['manager_id'])
                user.manager = user.validate_manager(manager)

            if payload.get('background_picture_id'):
                user.background_picture = UserUpload.lookup(tx, payload['background_picture_id'], user.customer_id)

            # TODO: (sunil) Error if current_skills was given but set to empty list
            if payload.get('current_skills'):
                User.validate_skills(payload['current_skills'], SkillType.CURRENT_SKILL)
                user.set_current_skills(tx, payload['current_skills'])

            # TODO: (sunil) Allow removing all desired_skills by setting to empty list
            if payload.get('desired_skills'):
                User.validate_skills(payload['desired_skills'], SkillType.DESIRED_SKILL)
                user.set_desired_skills(tx, payload['desired_skills'])

            user.update_profile(payload)

        # Fetch the user again from the database so the updates made above are reflected in the response
        with transaction() as tx:
            user = User.lookup(tx, user_id)
            user_details = user.as_dict()
        return user_details

    # @staticmethod
    # def delete(user_id):
    #     with transaction() as tx:
    #         user = tx.get(User, user_id)
    #         if user is None:
    #             # Noop if the user does not exist
    #             return {}
    #         tx.delete(user)
    #     return {}


class ProfilePictureAPIBase(AuthenticatedAPIBase, UserUploadMixin):

    @staticmethod
    def _put(user_id):
        # TODO: (sunil) add validation for accepted content types
        # user_id = current_cognito_jwt['sub']
        metadata = {
            'resource': 'user',
            'resource_id': user_id,
            'type': 'profile_picture',
        }
        return ProfilePictureAPIBase.create_user_upload(
            user_id, request.json['filename'], request.json['content_type'], 'users', metadata)


@blueprint.route('/<user_id>/profile_picture')
class ProfilePictureAPI(ProfilePictureAPIBase):

    @staticmethod
    def put(user_id):
        return ProfilePictureAPIBase._put(user_id)


class ProfilePictureByIdAPIBase(AuthenticatedAPIBase):

    @staticmethod
    def _put(user_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, user_id)
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            if status == UserUploadStatus.UPLOADED:
                user.profile_picture = user_upload
                user_upload.status = status.value
            # TODO: (sunil) return an error if this status transition is not supported

        return {
            'status': user_upload.status,
        }


@blueprint.route('/<user_id>/profile_picture/<upload_id>')
class ProfilePictureByIdAPI(ProfilePictureByIdAPIBase):

    @staticmethod
    def put(user_id, upload_id):
        return ProfilePictureByIdAPIBase._put(user_id, upload_id)


class BackgroundPictureAPIBase(AuthenticatedAPIBase, UserUploadMixin):

    @staticmethod
    def _put(user_id):
        metadata = {
            'resource': 'user',
            'resource_id': user_id,
            'type': 'background_picture',
        }
        return BackgroundPictureAPIBase.create_user_upload(
            user_id, request.json['filename'], request.json['content_type'], 'users', metadata)


@blueprint.route('/<user_id>/background_picture')
class BackgroundPictureAPI(BackgroundPictureAPIBase):

    @staticmethod
    def put(user_id):
        return BackgroundPictureAPIBase._put(user_id)


class BackgroundPictureByIdAPIBase(AuthenticatedAPIBase):

    @staticmethod
    def _put(user_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, user_id)
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            if status == UserUploadStatus.UPLOADED:
                user.background_picture = user_upload
                user_upload.status = status.value
        return {
            'status': user_upload.status,
        }


@blueprint.route('/<user_id>/background_picture/<upload_id>')
class BackgroundPictureByIdAPI(BackgroundPictureByIdAPIBase):

    @staticmethod
    def put(user_id, upload_id):
        return BackgroundPictureByIdAPIBase._put(user_id, upload_id)


@blueprint.route('/<user_id>/introduction_video')
class IntroductionVideoAPI(AuthenticatedAPIBase, UserUploadMixin):

    @staticmethod
    def put(user_id):
        metadata = {
            'resource': 'user',
            'resource_id': user_id,
            'type': 'introduction_video',
        }
        return IntroductionVideoAPI.create_user_upload(
            user_id, request.json['filename'], request.json['content_type'], 'users', metadata)


@blueprint.route('/<user_id>/introduction_video/<upload_id>')
class IntroductionVideoByIdAPI(AuthenticatedAPIBase):

    @staticmethod
    def put(user_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, user_id)
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            if status == UserUploadStatus.UPLOADED:
                user.introduction_video = user_upload
                user_upload.status = status.value

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(user_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)

            if user.id != user_id:
                raise NotAllowedError(f"User '{user.id}' cannot delete introduction video of user '{user_id}'")
            user.introduction_video = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()


@blueprint.route('/<user_id>/fun_fact')
class FunFactAPI(AuthenticatedAPIBase, UserUploadMixin):

    @staticmethod
    def put(user_id):
        # TODO: (sunil) add validation for accepted content types
        metadata = {
            'resource': 'user',
            'resource_id': user_id,
            'type': 'fun_fact',
        }
        return FunFactAPI.create_user_upload(
            user_id, request.json['filename'], request.json['content_type'], 'users', metadata)


@blueprint.route('/<user_id>/fun_fact/<upload_id>')
class FunFactByIdAPI(AuthenticatedAPIBase):

    @staticmethod
    def put(user_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, user_id)
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            if status == UserUploadStatus.UPLOADED:
                user.add_fun_fact(user_upload)
                user_upload.status = status.value
            # TODO: (sunil) return an error if this status transition is not supported

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(user_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)

            # For now, only the user is allowed to delete their fun fact
            if user.id != user_id:
                raise NotAllowedError(f"User '{user.id}' cannot delete fun fact of user '{user_id}'")
            user.fun_facts.remove(user_upload)
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()


@blueprint.route('/<user_id>/mentorship_video')
class MentorshipVideoAPI(AuthenticatedAPIBase, UserUploadMixin):

    @staticmethod
    def put(user_id):
        metadata = {
            'resource': 'user',
            'resource_id': user_id,
            'type': 'mentorship_video',
        }
        return MentorshipVideoAPI.create_user_upload(
            user_id, request.json['filename'], request.json['content_type'], 'users', metadata)


@blueprint.route('/<user_id>/mentorship_video/<upload_id>')
class MentorshipVideoByIdAPI(AuthenticatedAPIBase):

    @staticmethod
    def put(user_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, user_id)
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            if status == UserUploadStatus.UPLOADED:
                user.mentorship_video = user_upload
                user_upload.status = status.value

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(user_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)

            if user.id != user_id:
                raise NotAllowedError(f"User '{user.id}' cannot delete mentorship video of user '{user_id}'")
            user.mentorship_video = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()


@blueprint.route('/<user_id>/bookmark')
class UserBookmarkAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(user_id):
        with transaction() as tx:
            bookmarked_user = User.lookup(tx, user_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            bookmark = UserBookmark.lookup(tx, user.id, bookmarked_user.id, must_exist=False)
            if bookmark is None:
                UserBookmark(user=user, bookmarked_user=bookmarked_user, created_at=datetime.utcnow())
        return make_no_content_response()

    @staticmethod
    def delete(user_id):
        with transaction() as tx:
            bookmarked_user = User.lookup(tx, user_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            bookmark = UserBookmark.lookup(tx, user.id, bookmarked_user.id)
            tx.delete(bookmark)
        return make_no_content_response()
