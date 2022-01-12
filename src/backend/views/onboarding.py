from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint
from sqlalchemy import select

from backend.common.exceptions import InvalidArgumentError
from backend.models.db import transaction
from backend.models.product_preference import ProductPreference
from backend.models.user import User, SkillType
from backend.views.base import AuthenticatedAPIBase
from backend.views.user import (
    ProfilePictureAPIBase, ProfilePictureByIdAPIBase
)


blueprint = Blueprint('onboarding', __name__, url_prefix='/onboarding')


def set_onboarding_complete(user, onboarding_complete):
    profile = user.profile_copy
    if onboarding_complete:
        profile['onboarding_complete'] = True
    elif 'onboarding_complete' in profile:
        # In certain cases (e.g. "demo mode"),
        # a user may go through onboarding again after having already completed it
        del profile['onboarding_complete']
    user.profile = profile


@blueprint.route('/product_preferences')
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

            # Make sure onboarding is not marked as complete
            set_onboarding_complete(user, False)
        return jsonify([product.as_dict() for product in user.product_preferences])


@blueprint.route('/linkedin')
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
            user.profile = profile

            # Make sure onboarding is not marked as complete
            set_onboarding_complete(user, False)
        return {
            'linkedin_url': user.profile.get('linkedin_url', '')
        }


@blueprint.route('/current_skills')
class CurrentSkillAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        User.validate_skills(request.json, SkillType.CURRENT_SKILL)
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user.set_current_skills(tx, request.json)

            # Make sure onboarding is not marked as complete
            set_onboarding_complete(user, False)
        return jsonify([skill.as_dict() for skill in user.current_skills])


@blueprint.route('/desired_skills')
class DesiredSkillAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        User.validate_skills(request.json, SkillType.DESIRED_SKILL)
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user.set_desired_skills(tx, request.json)

            # Mark onboarding as complete
            set_onboarding_complete(user, True)
        return jsonify([skill.as_dict() for skill in user.desired_skills])


@blueprint.route('/profile_picture')
class ProfilePictureAPI(ProfilePictureAPIBase):
    @staticmethod
    def put():
        return ProfilePictureAPIBase._put(current_cognito_jwt['sub'])


@blueprint.route('/profile_picture/<upload_id>')
class ProfilePictureByIdAPI(ProfilePictureByIdAPIBase):
    @staticmethod
    def put(upload_id):
        response = ProfilePictureByIdAPIBase._put(current_cognito_jwt['sub'], upload_id)

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            # Make sure onboarding is not marked as complete
            set_onboarding_complete(user, False)

        return response
