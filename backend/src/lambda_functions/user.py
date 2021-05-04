"""AWS Lambda functions related to users"""

import pynamodb.exceptions
from base import registered_operations_handler
from common.decorators import register
from common.exceptions import DoesNotExistError, InvalidOperationError
from models.customer import Customer
from models.user import User, UserProfile

OPERATIONS_REGISTRY = {}

def user_operations_handler(event, context):
    """Handle user-related operations"""
    return registered_operations_handler(OPERATIONS_REGISTRY, event, context)

@register(OPERATIONS_REGISTRY, 'create_user')
def create_user_handler(event, context):
    """Create a new user within the given customer.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'name': 'Milton Waddams',
        'title': 'Stapler Evangelist',
        'profile_picture_url': 'http://example.com/profile.jpg',
        'skills': [{
            'name': 'Accounting Software',
            'level': 2
        }, {
            'name': 'Excel spreadsheet creation',
            'level': 3
        }, {
            'name': 'Machine Learning',
            'level': 1
        }],
        'skills_to_acquire': [{
            'name': 'Python programming',
            'level': 1
        }]
    }
    """
    profile = UserProfile()
    profile.name = event['name']
    profile.title = event.get('title')
    profile.picture_url = event.get('profile_picture_url')

    if event.get('skills', '') != '':
        User.validate_skills(event['skills'])
        profile.skills = event['skills']

    if event.get('skills_to_acquire', '') != '':
        User.validate_skills(event['skills_to_acquire'])
        profile.skills_to_acquire = event['skills_to_acquire']

    user = User(
        event['customer_id'],
        event['user_id'],
        profile=profile,
    )
    user.save()
    return user.as_dict()

@register(OPERATIONS_REGISTRY, 'list_users')
def list_users_handler(event, context):
    """Return all users. If a customer is specified, return all users for that customer.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1'
    }
    """
    if 'customer_id' not in event:
        return [user.as_dict() for user in User.scan()]
    return [user.as_dict() for user in User.query(event['customer_id'])]

@register(OPERATIONS_REGISTRY, 'get_user')
def get_user_handler(event, context):
    """Return details of a single user.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b'
    }
    """
    try:
        user = User.lookup(event['user_id'], event.get('customer_id'))
        customer = Customer.get(user.customer_id)
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError(f"User '{event['user_id']}' does not exist")

    user_details = user.as_dict()
    user_details['customer_name'] = customer.name
    return user_details

@register(OPERATIONS_REGISTRY, 'update_user')
def update_user_handler(event, context):
    """Update details of a single user.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'name': 'Peter Gibbons',
        'title': 'Unmotivated Programmer',
        'profile_picture_url': 'http://example.com/profile.jpg',
        'skills': [{
            'name': 'Accounting Software',
            'level': 2
        }, {
            'name': 'Excel spreadsheet creation',
            'level': 3
        }, {
            'name': 'Machine Learning',
            'level': 1
        }],
        'skills_to_acquire': [{
            'name': 'Python programming',
            'level': 1
        }]
    }
    """
    try:
        user = User.lookup(event['user_id'], event.get('customer_id'))
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError(f"User '{event['user_id']}' does not exist")

    if event.get('name', '') != '':
        user.profile.name = event['name']

    if event.get('title', '') != '':
        user.profile.title = event['title']

    if event.get('profile_picture_url', '') != '':
        user.profile.picture_url = event['profile_picture_url']

    if event.get('skills', '') != '':
        User.validate_skills(event['skills'])
        user.profile.skills = event['skills']

    if event.get('skills_to_acquire', '') != '':
        User.validate_skills(event['skills_to_acquire'])
        user.profile.skills_to_acquire = event['skills_to_acquire']

    user.save()
    return user.as_dict()

@register(OPERATIONS_REGISTRY, 'delete_user')
def delete_user_handler(event, context):
    """Delete a single user.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b'
    }
    """
    # TODO: (sunil) Add some checks for posts and any other resources linked to this user
    try:
        user = User.lookup(event['user_id'], event.get('customer_id'))
    except pynamodb.exceptions.DoesNotExist:
        # Noop if the user does not exist
        return
    user.delete()
