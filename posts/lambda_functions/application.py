"""AWS Lambda functions related to applications"""

import uuid

from common.exceptions import NotAllowedError
from models.application import Application
from models.post import Post
from models.user import User

def create_application_handler(event, context):
    """Create a new application for a post.

    Sample payload:
    {
        'post_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'applicant_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'summary': 'Additional information for this application'
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
        summary=event['summary']
    )
    application.save()
    return application.as_dict()

def list_applications_by_post_handler(event, context):
    """Return all applications for a post.

    Sample payload:
    {
        'post_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1'
    }
    """
    return Application.lookup_multiple(post_id=event['post_id'])

def list_applications_by_applicant_handler(event, context):
    """Return all applications for an applicant.

    Sample payload:
    {
        'applicant_id': '1cfa6354-580e-464e-b350-74d2c7b7793b'
    }
    """
    return Application.lookup_multiple(applicant_id=event['applicant_id'])

def get_application_handler(event, context):
    """Return details of a single application.

    Sample payload:
    {
        'application_id': '527d334d-8f99-4e73-bcd9-96cd4ff388d4'
    }
    """
    application = Application.lookup(event['application_id'])
    return application.as_dict()

def update_application_handler(event, context):
    """Update details of a single application.

    Sample payload:
    {
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'application_id': '527d334d-8f99-4e73-bcd9-96cd4ff388d4',
        'summary': 'Updated information for this application',
        'approval_status': 'none|approved|denied',
        'selection_status': 'none|rejected|shortlisted|selected'
    }
    """
    application = Application.lookup(event['application_id'])

    # TODO: (sunil) add authorization - 
    #   Only the post owner can update the selection status
    #   Only the manager of the applicant can update the approval status
    #   Only the applicant can update other values

    application.summary = event.get('summary', application.summary)
    application.save()
    return application.as_dict()

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
