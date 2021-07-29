import enum

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from sqlalchemy import select

from backend.common.exceptions import InvalidArgumentError
from backend.models.db import transaction
from backend.models.product_preference import ProductPreference
from backend.models.user import User, SkillType
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase


class OnboardingStep(enum.Enum):
    CHOOSE_PRODUCTS = 100
    CONNECT_LINKEDIN_ACCOUNT = 200
    SET_PROFILE_PICTURE = 300
    ADD_CURRENT_SKILLS = 400
    ADD_DESIRED_SKILLS = 500
    ONBOARDING_COMPLETE = 999


class ProductPreferenceAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            products = tx.execute(select(ProductPreference)).scalars().all()
        return jsonify([product.as_dict() for product in products])

    @staticmethod
    def post():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            try:
                product_ids = [product['product_id'] for product in request.json]
            except KeyError as ex:
                raise InvalidArgumentError("Invalid format: product_id is missing") from ex

            # Lookup the products and make sure they all exist in the database
            products_selected = ProductPreference.lookup_multiple(tx, product_ids)

            # TODO: (sunil) Need to lock the user here so no other thread can make updates

            # User may have already selected some products,
            # remove any product that's not in the new list, then add the rest
            products_to_remove = set(user.product_preferences) - set(products_selected)
            for product in products_to_remove:
                user.product_preferences.remove(product)

            products_to_add = set(products_selected) - set(user.product_preferences)
            for product in products_to_add:
                user.product_preferences.append(product)

            # Move the onboarding workflow to the next step
            profile = user.profile_copy
            onboarding = profile.setdefault('onboarding_steps', {})
            onboarding['current'] = OnboardingStep.CONNECT_LINKEDIN_ACCOUNT.value
            user.profile = profile
        return jsonify([product.as_dict() for product in user.product_preferences])


class LinkedInAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        linkedin_url = request.json.get('linkedin_url')
        if linkedin_url is None:
            raise InvalidArgumentError('linkedin_url is missing')

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            profile = user.profile_copy
            if linkedin_url:
                profile['linkedin_url'] = linkedin_url
            elif 'linkedin_url' in profile:
                # If there was an existing value for LinkedIn URL, and it's now
                # being set to empty string, remove it instead
                del profile['linkedin_url']

            onboarding = profile.setdefault('onboarding_steps', {})
            onboarding['current'] = OnboardingStep.SET_PROFILE_PICTURE.value
            user.profile = profile
        return {
            'linkedin_url': user.profile.get('linkedin_url', '')
        }


class CurrentSkillAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        User.validate_skills(request.json, SkillType.CURRENT_SKILL)
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user.set_current_skills(tx, request.json)

            # Move the onboarding workflow to the next step
            profile = user.profile_copy
            onboarding = profile.setdefault('onboarding_steps', {})
            onboarding['current'] = OnboardingStep.ADD_DESIRED_SKILLS.value
            user.profile = profile
        return jsonify([skill.as_dict() for skill in user.current_skills])


class DesiredSkillAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        User.validate_skills(request.json, SkillType.DESIRED_SKILL)
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user.set_desired_skills(tx, request.json)

            # Move the onboarding workflow to the next step
            profile = user.profile_copy
            onboarding = profile.setdefault('onboarding_steps', {})
            onboarding['current'] = OnboardingStep.ONBOARDING_COMPLETE.value
            user.profile = profile
        return jsonify([skill.as_dict() for skill in user.desired_skills])


class ProfilePictureAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put():
        # TODO: (sunil) add validation for accepted content types
        user_id = current_cognito_jwt['sub']
        metadata = {
            'resource': 'user',
            'resource_id': user_id,
            'type': 'profile_picture',
        }
        return ProfilePictureAPI.create_user_upload(
            user_id, request.json['filename'], request.json['content_type'], 'users', metadata)


class ProfilePictureByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            if status == UserUploadStatus.UPLOADED:
                user.profile_picture = user_upload
                user_upload.status = status.value
            # TODO: (sunil) return an error if this status transition is not supported

            profile = user.profile_copy
            onboarding = profile.setdefault('onboarding_steps', {})
            onboarding['current'] = OnboardingStep.ADD_CURRENT_SKILLS.value
            user.profile = profile

        return {
            'status': user_upload.status,
        }
