from flask import jsonify, request
from flask_cognito import cognito_auth_required

from app import app
from models.db import transaction
from models.skill import Skill

@app.route('/skills')
@cognito_auth_required
def search_skills_handler():
    with transaction() as tx:
        skills = Skill.search(tx, query=request.args.get('q'))
    return jsonify(skills)
