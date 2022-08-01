from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.http import make_no_content_response
from backend.common.exceptions import InvalidArgumentError
from backend.common.datetime import DateTime

from backend.models.db import transaction
from backend.models.user import User
from backend.models.project import Project, ProjectStatus, ProjectClient

from backend.views.base import AuthenticatedAPIBase

from backend.models.activities import Activity, ActivityGlobal, ActivityType


blueprint = Blueprint('project', __name__, url_prefix='/projects')


@blueprint.route('')
class ProjectAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            # This is the user making the request, for authorization purposes
            user = User.lookup(tx, current_cognito_jwt['sub'])
            
            client = ProjectClient.lookup(tx, request.args.get('client_id')) if 'client_id' in request.args else None
            keyword = request.args.get('keyword', None)

            positions = Project.search(
                tx,
                user,
                client=client,
                keyword=keyword
            )
            positions = [position.as_dict() for position in positions]
        return jsonify(positions)

    @staticmethod
    def post():
        payload = request.json

        project_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {
            'manager_id', 'client_id', 'start_date', 'description'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        start_date = DateTime.validate_and_convert_isoformat_to_date(
            request.args.get('start_date'), 'start_date') if 'start_date' in request.args else None

        with transaction() as tx:
            client = ProjectClient.lookup(tx, payload['client_id'])
            manager = User.lookup(tx, payload['manager_id'])

            project = Project(
                id=project_id,
                client=client,
                manager=manager,
                status=ProjectStatus.ACTIVE.value,
                start_date=start_date,
                created_at=now,
                last_updated_at=now
            )
            project.update_details(payload)
            tx.add(project)

            # Insert activity details in DB
            activity_data = {
                'project': {
                    'project_id': project.id
                },
                'user': {
                    'user_id': project.manager.id,
                    'name': project.manager.name,
                    'profile_picture_url': project.manager.profile_picture_url
                }
            }
            tx.add(Activity.add_activity(project.manager, ActivityType.NEW_PROJECT_POSTED, data=activity_data))
            tx.add(ActivityGlobal.add_activity(
                project.hiring_manager.customer, ActivityType.NEW_PROJECT_POSTED, data=activity_data))

            project_details = project.as_dict()

        return project_details


@blueprint.route('/<project_id>')
class ProjectByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(project_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            position = Project.lookup(tx, project_id, user)
            return position.as_dict()
