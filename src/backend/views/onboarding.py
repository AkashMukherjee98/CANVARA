from datetime import datetime
import enum
import uuid

from flask import jsonify, request
from flask.views import MethodView
from flask_cognito import current_cognito_jwt
from sqlalchemy import select

from backend.common.exceptions import InvalidArgumentError
from backend.common.http import make_no_content_response
from backend.models.db import transaction
from backend.models.product_preference import ProductPreference
from backend.models.user import User, SkillType
from backend.models.user_upload import UserUpload, UserUploadStatus


class OnboardingStep(enum.Enum):
    CHOOSE_PRODUCTS = 100
    CONNECT_LINKEDIN_ACCOUNT = 200
    SET_PROFILE_PICTURE = 300
    ADD_CURRENT_SKILLS = 400
    ADD_DESIRED_SKILLS = 500
    ONBOARDING_COMPLETE = 999


class ProductPreferenceAPI(MethodView):
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
        return make_no_content_response()


class LinkedInAPI(MethodView):
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
            elif profile['linkedin_url']:
                # If there was an existing value for LinkedIn URL, and it' now
                # being set to empty string, remove it instead
                del profile['linkedin_url']

            onboarding = profile.setdefault('onboarding_steps', {})
            onboarding['current'] = OnboardingStep.SET_PROFILE_PICTURE.value
            user.profile = profile
        return make_no_content_response()


class CurrentSkillAPI(MethodView):
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
        return make_no_content_response()


class DesiredSkillAPI(MethodView):
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
        return make_no_content_response()


class ProfilePictureAPI(MethodView):
    @staticmethod
    def put():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            customer_id = user.customer_id

        # TODO: (sunil) add validation for accepted content types
        original_filename = request.json['filename']
        content_type = request.json['content_type']
        bucket = UserUpload.get_bucket_name()
        path = UserUpload.generate_upload_path(customer_id, 'users', original_filename)
        presigned_url = UserUpload.generate_presigned_put_url(bucket, path, content_type)

        now = datetime.utcnow()
        with transaction() as tx:
            user_upload = UserUpload(
                id=str(uuid.uuid4()),
                customer_id=customer_id,
                bucket=bucket,
                path=path,
                content_type=content_type,
                status=UserUploadStatus.CREATED.value,
                metadata={
                    'user_id': user.id,
                    'original_filename': original_filename,
                    'resource': 'user',
                    'resource_id': user.id,
                    'type': 'profile_picture',
                },
                created_at=now
            )
            tx.add(user_upload)

        return {
            'upload_id': user_upload.id,
            'url': presigned_url,
        }


class ProfilePictureByIdAPI(MethodView):
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
