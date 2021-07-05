import enum

from flask import jsonify, request
from flask.views import MethodView
from flask_cognito import current_cognito_jwt
from sqlalchemy import select

from backend.common.exceptions import InvalidArgumentError
from backend.common.http import make_no_content_response
from backend.models.db import transaction
from backend.models.product_preference import ProductPreference
from backend.models.user import User, SkillType


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
