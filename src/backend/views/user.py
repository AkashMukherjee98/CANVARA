import copy

from flask import current_app as app
from flask import jsonify, request
from flask_cognito import cognito_auth_required

from sqlalchemy import select

from backend.models.db import transaction
from backend.models.user import User, SkillType


@app.route('/customers/<customer_id>/users', methods=['POST'])
@cognito_auth_required
def create_user_handler(customer_id):
    payload = request.json
    profile = {}
    if payload.get('title'):
        profile['title'] = payload['title']

    if payload.get('profile_picture_url'):
        profile['profile_picture_url'] = payload.get('profile_picture_url')

    user = User(
        id=payload['user_id'],
        customer_id=customer_id,
        name=payload['name'],
        profile=profile,
    )
    with transaction() as tx:
        tx.add(user)

        if payload.get('current_skills'):
            User.validate_skills(payload['current_skills'], SkillType.CURRENT_SKILL)
            user.set_current_skills(tx, payload['current_skills'])

        if payload.get('desired_skills'):
            User.validate_skills(payload['desired_skills'], SkillType.DESIRED_SKILL)
            user.set_desired_skills(tx, payload['desired_skills'])

        user_details = user.as_dict()
    return user_details


@app.route('/customers/<customer_id>/users')
@cognito_auth_required
def list_users_handler(customer_id):
    with transaction() as tx:
        users = tx.execute(select(User).where(User.customer_id == customer_id)).scalars().all()
        user_details = jsonify([user.as_dict() for user in users])
    return user_details


@app.route('/users/<user_id>')
@cognito_auth_required
def get_user_handler(user_id):
    with transaction() as tx:
        user = User.lookup(tx, user_id)
        user_details = user.as_dict()
        user_details['customer_name'] = user.customer.name
    return user_details


@app.route('/users/<user_id>', methods=['PUT'])
@cognito_auth_required
def update_user_handler(user_id):
    with transaction() as tx:
        user = User.lookup(tx, user_id)

        payload = request.json
        if payload.get('name'):
            user.name = payload['name']

        if payload.get('current_skills'):
            User.validate_skills(payload['current_skills'], SkillType.CURRENT_SKILL)
            user.set_current_skills(tx, payload['current_skills'])

        if payload.get('desired_skills'):
            User.validate_skills(payload['desired_skills'], SkillType.DESIRED_SKILL)
            user.set_desired_skills(tx, payload['desired_skills'])

        profile = copy.deepcopy(user.profile)
        if payload.get('title'):
            profile['title'] = payload['title']

        if payload.get('profile_picture_url'):
            profile['profile_picture_url'] = payload['profile_picture_url']

        user.profile = profile

    # Fetch the user again from the database so the updates made above are reflected in the response
    with transaction() as tx:
        user = User.lookup(tx, user_id)
        user_details = user.as_dict()
    return user_details

# @app.route('/users/<user_id>', methods=['DELETE'])
# @cognito_auth_required
# def delete_user_handler(user_id):
#     with transaction() as tx:
#         user = tx.get(User, user_id)
#         if user is None:
#             # Noop if the user does not exist
#             return {}
#         tx.delete(user)
#     return {}
