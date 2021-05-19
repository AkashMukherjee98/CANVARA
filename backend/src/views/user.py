from flask import jsonify, request
from flask_cognito import cognito_auth_required

import pynamodb.exceptions
from common.exceptions import DoesNotExistError
from models.customer import Customer
from models.user import User, UserProfile
from app import app

@app.route('/customers/<customer_id>/users', methods=['POST'])
@cognito_auth_required
def create_user_handler(customer_id):
    payload = request.json
    profile = UserProfile()
    profile.name = payload['name']
    profile.title = payload.get('title')
    profile.picture_url = payload.get('profile_picture_url')

    if payload.get('skills'):
        User.validate_skills(payload['skills'])
        profile.skills = payload['skills']

    if payload.get('skills_to_acquire'):
        User.validate_skills(payload['skills_to_acquire'])
        profile.skills_to_acquire = payload['skills_to_acquire']

    user = User(
        customer_id,
        payload['user_id'],
        profile=profile,
    )
    user.save()
    return user.as_dict()

@app.route('/customers/<customer_id>/users')
@cognito_auth_required
def list_users_handler(customer_id):
    return jsonify([user.as_dict() for user in User.query(customer_id)])

@app.route('/users/<user_id>')
@cognito_auth_required
def get_user_handler(user_id):
    try:
        user = User.lookup(user_id)
        customer = Customer.get(user.customer_id)
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError(f"User '{user_id}' does not exist")

    user_details = user.as_dict()
    user_details['customer_name'] = customer.name
    return user_details

@app.route('/users/<user_id>', methods=['PUT'])
@cognito_auth_required
def update_user_handler(user_id):
    payload = request.json
    try:
        user = User.lookup(user_id)
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError(f"User '{user_id}' does not exist")

    if payload.get('name'):
        user.profile.name = payload['name']

    if payload.get('title'):
        user.profile.title = payload['title']

    if payload.get('profile_picture_url'):
        user.profile.picture_url = payload['profile_picture_url']

    if payload.get('skills'):
        User.validate_skills(payload['skills'])
        user.profile.skills = payload['skills']

    if payload.get('skills_to_acquire'):
        User.validate_skills(payload['skills_to_acquire'])
        user.profile.skills_to_acquire = payload['skills_to_acquire']

    user.save()
    return user.as_dict()


# @app.route('/users/<user_id>', methods=['DELETE'])
# @cognito_auth_required
# def delete_user_handler(user_id):
#     user.delete_user(user_id)
#     return {}
