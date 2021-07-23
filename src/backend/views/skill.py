from flask import jsonify, request
from flask_cognito import current_cognito_jwt

from backend.models.db import transaction
from backend.models.skill import Skill
from backend.models.user import User
from backend.views.base import AuthenticatedAPIBase


class SkillAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            # TODO: (sunil) Pass current user id to Skill.search and let it join
            #               with user table instead of executing two queries
            user = User.lookup(tx, current_cognito_jwt['sub'])
            skills = Skill.search(tx, user.customer_id, query=request.args.get('q'))
        return jsonify(skills)
