import uuid

from flask import jsonify, request
from flask_cognito import cognito_auth_required, current_cognito_jwt

from common.exceptions import NotAllowedError
from models.application import Application
from models.post import Post
from models.user import User
from app import app

@app.route('/posts/<post_id>/applications', methods=['POST'])
@cognito_auth_required
def create_application_handler(post_id):
    # Make sure the user and the post exist
    applicant = User.lookup(current_cognito_jwt['sub'])
    post = Post.lookup(applicant.customer_id, post_id)

    payload = request.json

    # TODO: (sunil) Make sure the post is active
    # TODO: (sunil) Make sure there isn't already an application by this post+applicant

    # Generate a unique id for this post
    application_id = str(uuid.uuid4())

    application = Application(
        post.post_id,
        applicant.user_id,
        application_id=application_id,
        description=payload['description'],
        status=Application.Status.NEW.value
    )
    application.save()
    return application.as_dict()

@app.route('/posts/<post_id>/applications')
@cognito_auth_required
def list_applications_by_post_handler(post_id):
    return jsonify(Application.lookup_multiple(post_id=post_id))

@app.route('/applications')
@cognito_auth_required
def list_applications_by_applicant_handler():
    return jsonify(Application.lookup_multiple(applicant_id=current_cognito_jwt['sub']))

@app.route('/applications/<application_id>')
@cognito_auth_required
def get_application_handler(application_id):
    application = Application.lookup(application_id)
    return application.as_dict()

@app.route('/applications/<application_id>', methods=['PUT'])
@cognito_auth_required
def update_application_handler(application_id):
    application = Application.lookup(application_id)
    payload = request.json

    # TODO: (sunil) add authorization - 
    #   Only the post owner can change status to rejected/shortlisted/selected
    #   Only the manager of the applicant can change status to approved or denied
    #   Only the applicant can update other values

    if payload.get('description'):
        application.description = payload['description']

    # TODO: (sunil) enforce correct state transitions
    if payload.get('status'):
        Application.validate_status(payload['status'])
        application.status = payload['status']

    application.save()
    return application.as_dict()

@app.route('/applications/<application_id>', methods=['DELETE'])
@cognito_auth_required
def delete_application_handler(application_id):
    application = Application.lookup(application_id, must_exist=False)

    if application is None:
        # Noop if the application does not exist
        return

    # For now, only the applicant is allowed to delete the application
    user_id = current_cognito_jwt['sub']
    if application.applicant_id != user_id:
        raise NotAllowedError(f"User '{user_id}' is not the applicant")

    application.delete()
    return {}
