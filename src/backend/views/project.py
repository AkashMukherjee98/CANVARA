from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.exceptions import InvalidArgumentError

from backend.models.db import transaction
from backend.models.user import User
from backend.models.project import Project, ProjectStatus
from backend.models.client import Client

from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('project', __name__, url_prefix='/projects')


@blueprint.route('')
class ProjectAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        payload = request.json
        project_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {'name', 'client_id'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            client = Client.lookup(tx, payload.get('client_id'))

            project = Project(
                id=project_id,
                customer_id=user.customer_id,
                name=payload.get('name'),
                client=client,
                status=ProjectStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(project)

            project_details = project.as_dict()

        return project_details

    @staticmethod
    def get():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            projects = Project.search(
                tx,
                user.customer_id
            )
            projects = [project.as_dict() for project in projects]
        return jsonify(projects)


@blueprint.route('/<project_id>')
class ProjectByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(project_id):
        payload = request.json
        now = datetime.utcnow()

        with transaction() as tx:
            project = Project.lookup(tx, project_id)

            if payload.get('name'):
                project.name = payload['name']

            project.last_updated_at = now

        with transaction() as tx:
            project = Project.lookup(tx, project_id)
            project_details = project.as_dict()
        return project_details
