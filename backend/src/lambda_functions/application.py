"""AWS Lambda functions related to applications"""

import uuid

from base import registered_operations_handler
from common.decorators import register
from common.exceptions import NotAllowedError
from models.application import Application
from models.post import Post
from models.user import User

OPERATIONS_REGISTRY = {}

def application_operations_handler(event, context):
    """Handle application-related operations"""
    return registered_operations_handler(OPERATIONS_REGISTRY, event, context)

@register(OPERATIONS_REGISTRY, 'create_application')
def create_application_handler(event, context):
    """Create a new application for a post.

    Sample payload:
    {
        'post_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'applicant_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'description': 'Additional information for this application'
    }
    """
    # Make sure the user and the post exist
    applicant = User.lookup(event['applicant_id'])
    post = Post.lookup(applicant.customer_id, event['post_id'])

    # TODO: (sunil) Make sure the post is active
    # TODO: (sunil) Make sure there isn't already an application by this post+applicant

    # Generate a unique id for this post
    application_id = str(uuid.uuid4())

    application = Application(
        post.post_id,
        applicant.user_id,
        application_id=application_id,
        description=event['description'],
        status=Application.Status.NEW.value
    )
    application.save()
    return application.as_dict()

@register(OPERATIONS_REGISTRY, 'list_applications_by_post')
def list_applications_by_post_handler(event, context):
    """Return all applications for a post.

    Sample payload:
    {
        'post_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1'
    }
    """
    return Application.lookup_multiple(post_id=event['post_id'])

@register(OPERATIONS_REGISTRY, 'list_applications_by_applicant')
def list_applications_by_applicant_handler(event, context):
    """Return all applications for an applicant.

    Sample payload:
    {
        'applicant_id': '1cfa6354-580e-464e-b350-74d2c7b7793b'
    }
    """
    return Application.lookup_multiple(applicant_id=event['applicant_id'])

@register(OPERATIONS_REGISTRY, 'get_application')
def get_application_handler(event, context):
    """Return details of a single application.

    Sample payload:
    {
        'application_id': '527d334d-8f99-4e73-bcd9-96cd4ff388d4'
    }
    """
    application = Application.lookup(event['application_id'])
    return application.as_dict()

@register(OPERATIONS_REGISTRY, 'update_application')
def update_application_handler(event, context):
    """Update details of a single application.

    Sample payload:
    {
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'application_id': '527d334d-8f99-4e73-bcd9-96cd4ff388d4',
        'description': 'Updated information for this application',
        'status': 'approved'
    }
    """
    application = Application.lookup(event['application_id'])

    # TODO: (sunil) add authorization - 
    #   Only the post owner can change status to rejected/shortlisted/selected
    #   Only the manager of the applicant can change status to approved or denied
    #   Only the applicant can update other values

    if event.get('description', '') != '':
        application.description = event['description']

    # TODO: (sunil) enforce correct state transitions
    if event.get('status', '') != '':
        Application.validate_status(event['status'])
        application.status = event['status']

    application.save()
    return application.as_dict()

@register(OPERATIONS_REGISTRY, 'delete_application')
def delete_application_handler(event, context):
    """Delete a single application.

    Sample payload:
    {
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'application_id': '527d334d-8f99-4e73-bcd9-96cd4ff388d4'
    }
    """
    application = Application.lookup(event['application_id'], must_exist=False)

    if application is None:
        # Noop if the application does not exist
        return

    # For now, only the applicant is allowed to delete the application
    if application.applicant_id != event['user_id']:
        raise NotAllowedError(f"User '{event['user_id']}' is not the applicant")

    application.delete()
