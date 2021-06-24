from flask import current_app as app
from flask import jsonify, request
from flask_cognito import cognito_auth_required

from backend.models.db import transaction
from backend.models.skill import Skill


@app.route('/skills')
@cognito_auth_required
def search_skills_handler():
    with transaction() as tx:
        skills = Skill.search(tx, query=request.args.get('q'))
    return jsonify(skills)
