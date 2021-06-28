from flask import current_app as app
from flask import jsonify, request
from flask_cognito import cognito_auth_required, current_cognito_jwt

from backend.models.db import transaction
from backend.models.skill import Skill
from backend.models.user import User


@app.route('/skills')
@cognito_auth_required
def search_skills_handler():
    with transaction() as tx:
        # TODO: (sunil) Pass current user id to Skill.search and let it join with user table instead of executing two queries
        user = User.lookup(tx, current_cognito_jwt['sub'])
        skills = Skill.search(tx, user.customer_id, query=request.args.get('q'))
    return jsonify(skills)
