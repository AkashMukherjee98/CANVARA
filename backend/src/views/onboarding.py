import enum

from flask import jsonify, request
from flask_cognito import cognito_auth_required, current_cognito_jwt
from sqlalchemy import select

from app import app
from common.exceptions import InvalidArgumentError
from common.http import make_no_content_response
from models.db import transaction
from models.product_preference import ProductPreference
from models.user import User

class OnboardingStep(enum.Enum):
    CHOOSE_PRODUCTS = 100
    CONNECT_LINKEDIN_ACCOUNT = 200
    SET_PROFILE_PICTURE = 300
    ADD_SKILLS = 400
    ADD_DESIRED_SKILLS = 500

@app.route('/onboarding/product_preferences')
@cognito_auth_required
def list_products_handler():
    with transaction() as tx:
        products = tx.execute(select(ProductPreference)).scalars().all()
    return jsonify([product.as_dict() for product in products])

@app.route('/onboarding/product_preferences', methods=['POST'])
@cognito_auth_required
def set_product_preferences_handler():
    with transaction() as tx:
        user = User.lookup(tx, current_cognito_jwt['sub'])

        try:
            product_ids = [product['product_id'] for product in request.json]
        except KeyError:
            raise InvalidArgumentError("Invalid format: product_id is missing")

        # Lookup the products and make sure they all exist in the database
        products_selected = ProductPreference.lookup_multiple(tx, product_ids)

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
