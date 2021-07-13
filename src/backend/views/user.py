import copy

from flask import jsonify, request
from flask.views import MethodView
from flask_cognito import current_cognito_jwt

from sqlalchemy import select

from backend.models.db import transaction
from backend.models.user import User, SkillType


class CustomerUserAPI(MethodView):
    @staticmethod
    def get(customer_id):
        with transaction() as tx:
            users = tx.execute(select(User).where(User.customer_id == customer_id)).scalars().all()
            user_details = jsonify([user.as_dict() for user in users])
        return user_details

    @staticmethod
    def post(customer_id):
        payload = request.json
        profile = {}
        if payload.get('title'):
            profile['title'] = payload['title']

        if payload.get('linkedin_url') is not None:
            profile['linkedin_url'] = payload['linkedin_url']

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


class UserAPI(MethodView):
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

            # TODO: (sunil) Error if current_skills was given but set to empty list
            if payload.get('current_skills'):
                User.validate_skills(payload['current_skills'], SkillType.CURRENT_SKILL)
                user.set_current_skills(tx, payload['current_skills'])

            # TODO: (sunil) Allow removing all desired_skills by setting to empty list
            if payload.get('desired_skills'):
                User.validate_skills(payload['desired_skills'], SkillType.DESIRED_SKILL)
                user.set_desired_skills(tx, payload['desired_skills'])

            profile = copy.deepcopy(user.profile)
            if payload.get('title'):
                profile['title'] = payload['title']

            if payload.get('linkedin_url') is not None:
                if payload['linkedin_url']:
                    profile['linkedin_url'] = payload['linkedin_url']
                elif profile['linkedin_url']:
                    # If there was an existing value for LinkedIn URL, and it' now
                    # being set to empty string, remove it instead
                    del profile['linkedin_url']

            user.profile = profile

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
