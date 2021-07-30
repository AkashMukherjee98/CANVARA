from flask import jsonify, request
from flask_cognito import current_cognito_jwt

from sqlalchemy import select

from backend.common.exceptions import NotAllowedError
from backend.common.http import make_no_content_response
from backend.models.db import transaction
from backend.models.location import Location
from backend.models.user import User, SkillType
from backend.views.base import AuthenticatedAPIBase
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin


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

            if payload.get('location_id'):
                user.location = Location.lookup(tx, payload['location_id'])

            if payload.get('current_skills'):
                User.validate_skills(payload['current_skills'], SkillType.CURRENT_SKILL)
                user.set_current_skills(tx, payload['current_skills'])

            if payload.get('desired_skills'):
                User.validate_skills(payload['desired_skills'], SkillType.DESIRED_SKILL)
                user.set_desired_skills(tx, payload['desired_skills'])

            user_details = user.as_dict()
        return user_details


class UserAPI(AuthenticatedAPIBase):
    @staticmethod
    def __get_user(user_id):
        with transaction() as tx:
            user = User.lookup(tx, user_id)
            user_details = user.as_dict()
            user_details['customer_name'] = user.customer.name
        return user_details

    @staticmethod
    def __get_current_user():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_details = user.as_dict()
            user_details['customer_name'] = user.customer.name
        return user_details

    @staticmethod
    def get(user_id=None):
        if user_id is not None:
            return UserAPI.__get_user(user_id)

        return UserAPI.__get_current_user()

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

            if payload.get('location_id'):
                user.location = Location.lookup(tx, payload['location_id'])

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


class ProfilePictureByIdAPI(ProfilePictureByIdAPIBase):
    @staticmethod
    def put(user_id, upload_id):
        return ProfilePictureByIdAPIBase._put(user_id, upload_id)


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
            tx.delete(user_upload)
        return make_no_content_response()
