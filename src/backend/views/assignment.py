from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.http import make_no_content_response
from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.common.datetime import DateTime

from backend.models.db import transaction
from backend.models.user import User
from backend.models.location import Location
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.models.project import Project
from backend.models.assignment import Assignment, AssignmentStatus, AssignmentSortFilter, AssignmentBookmark
from backend.models.assignment import AssignmentApplication, AssignmentApplicationStatus, AssignmentApplicationFilter

from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase

from backend.models.activities import Activity, ActivityGlobal, ActivityType

blueprint = Blueprint('assignment', __name__, url_prefix='/assignments')


@blueprint.route('')
class AssignmentAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        payload = request.json
        assignment_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {'name', 'people_needed', 'start_date'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        start_date = DateTime.validate_and_convert_isoformat_to_date(payload['start_date'], 'start_date')

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            project = Project.lookup(tx, payload['project_id'])
            location = Location.lookup(tx, payload['location_id'])

            assignment = Assignment(
                id=assignment_id,
                customer_id=user.customer.id,
                creator=user,
                project=project,
                location=location,
                name=payload.get('name'),
                role=payload.get('role', None),
                start_date=start_date,
                people_needed=payload.get('people_needed'),
                status=AssignmentStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(assignment)
            assignment.update_details(payload)

            if payload.get('required_skills'):
                Assignment.validate_skills(payload['required_skills'])
                assignment.set_skills(tx, payload['required_skills'])

            # Insert activity details in DB
            activity_data = {
                'assignment': {
                    'assignment_id': assignment.id,
                    'name': assignment.name
                },
                'user': {
                    'user_id': assignment.creator.id,
                    'name': assignment.creator.name,
                    'profile_picture_url': assignment.creator.profile_picture_url
                }
            }
            tx.add(Activity.add_activity(assignment.creator, ActivityType.NEW_ASSIGNMENT_CREATED, data=activity_data))
            tx.add(ActivityGlobal.add_activity(
                user.customer, ActivityType.NEW_ASSIGNMENT_CREATED, data=activity_data))

            assignment_details = assignment.as_dict()

        return assignment_details

    @staticmethod
    def get():
        sort = AssignmentSortFilter.lookup(request.args.get('sort')) if 'sort' in request.args else None
        keyword = request.args.get('keyword', None)

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            location = Location.lookup(tx, request.args.get('location_id')) if 'location_id' in request.args else None

            assignments = Assignment.search(
                tx,
                user,
                sort=sort,
                keyword=keyword,
                location=location
            )
            assignments = [assignment.as_dict() for assignment in assignments]
        return jsonify(assignments)


@blueprint.route('/<assignment_id>')
class AssignmentByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(assignment_id):
        now = datetime.utcnow()

        with transaction() as tx:
            assignment = Assignment.lookup(tx, assignment_id)

            payload = request.json

            if payload.get('name'):
                assignment.name = payload['name']

            if payload.get('location_id'):
                assignment.location = Location.lookup(tx, payload['location_id'])

            if 'status' in payload:
                new_status = AssignmentStatus.lookup(payload['status'])
                if assignment.status != new_status:
                    assignment.status = new_status.value

            assignment.last_updated_at = now
            assignment.update_details(payload)

            if payload.get('required_skills'):
                Assignment.validate_skills(payload['required_skills'])
                assignment.set_skills(tx, payload['required_skills'])

        # Fetch from the database to get updated response
        with transaction() as tx:
            assignment = Assignment.lookup(tx, assignment_id)
            assignment_details = assignment.as_dict()
        return assignment_details

    @staticmethod
    def get(assignment_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            assignment = Assignment.lookup(tx, assignment_id, user)
            return assignment.as_dict()

    @staticmethod
    def delete(assignment_id):
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            assignment = Assignment.lookup(tx, assignment_id)

            # For now, only the creator is allowed to delete the assignment
            if assignment.creator != user:
                raise NotAllowedError(f"User '{user.id}' is not the assignment creator")
            assignment.status = AssignmentStatus.DELETED.value
            assignment.last_updated_at = now
        return make_no_content_response()


@blueprint.route('/<assignment_id>/video_description')
class AssignmentVideoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(assignment_id):
        metadata = {
            'resource': 'assignment',
            'resource_id': assignment_id,
            'type': 'assignment_video',
        }
        return AssignmentVideoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'assignments', metadata)


@blueprint.route('/<assignment_id>/video_description/<upload_id>')
class AssignmentVideoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(assignment_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            assignment = Assignment.lookup(tx, assignment_id)
            if status == UserUploadStatus.UPLOADED:
                assignment.video_description_id = user_upload.id
                user_upload.status = status.value

            return {
                'status': user_upload.status,
            }

    @staticmethod
    def delete(assignment_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            assignment = Assignment.lookup(tx, assignment_id)

            assignment.video_description_id = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()


@blueprint.route('/<assignment_id>/bookmark')
class AssignmentBookmarkAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(assignment_id):
        with transaction() as tx:
            assignment = Assignment.lookup(tx, assignment_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            bookmark = AssignmentBookmark.lookup(tx, user.id, assignment.id, must_exist=False)
            if bookmark is None:
                AssignmentBookmark(user=user, assignment=assignment, created_at=datetime.utcnow())
        return make_no_content_response()

    @staticmethod
    def delete(assignment_id):
        with transaction() as tx:
            assignment = Assignment.lookup(tx, assignment_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            bookmark = AssignmentBookmark.lookup(tx, user.id, assignment.id)
            tx.delete(bookmark)
        return make_no_content_response()


@blueprint.route('/<assignment_id>/applications')
class AssignmentApplicationAPI(AuthenticatedAPIBase):
    @staticmethod
    def post(assignment_id):
        payload = request.json
        application_id = str(uuid.uuid4())
        now = datetime.utcnow()

        mandatory_fields = {'description'}
        missing_fields = mandatory_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            assignment = Assignment.lookup(tx, assignment_id)
            application = AssignmentApplication(
                id=application_id,
                assignment=assignment,
                applicant=user,
                status=AssignmentApplicationStatus.NEW.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(application)
            application.update_details(payload)

            application_details = application.as_dict()

        return application_details

    @staticmethod
    def get(assignment_id):
        application_filter = AssignmentApplicationFilter.lookup(request.args.get('filter'))

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            applications = AssignmentApplication.search(
                tx,
                user,
                assignment_id,
                application_filter=application_filter
            )
            applications = [application.as_dict() for application in applications]
        return jsonify(applications)


@blueprint.route('/applications/<application_id>')
class AssignmentApplicationByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(application_id):
        with transaction() as tx:
            application = AssignmentApplication.lookup(tx, application_id)
            return application.as_dict()

    @staticmethod
    def put(application_id):
        now = datetime.utcnow()

        with transaction() as tx:
            application = AssignmentApplication.lookup(tx, application_id)
            payload = request.json

            application.update_details(payload)

            if 'status' in payload:
                new_status = AssignmentApplicationStatus.lookup(payload['status'])

                if application.status != new_status:
                    application.status = new_status.value

                    if new_status in [AssignmentApplicationStatus.SELECTED, AssignmentApplicationStatus.REJECTED]:
                        application.decided_at = now

            application.last_updated_at = now

        # Fetch from the database to get updated response
        with transaction() as tx:
            application = AssignmentApplication.lookup(tx, application_id)
            application_details = application.as_dict()
        return application_details

    @staticmethod
    def delete(application_id):
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            application = AssignmentApplication.lookup(tx, application_id)

            # For now, only the applicant is allowed to delete the application
            if application.applicant_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the creator of this application")
            application.status = AssignmentApplicationStatus.DELETED.value
            application.last_updated_at = now
        return make_no_content_response()
