"""AWS Lambda functions related to users"""

import uuid

import pynamodb.exceptions
from common.exceptions import DoesNotExistError
from models.user import User

def create_user_handler(event, context):
    """Create a new user within the given customer.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'name': 'Milton Waddams'
    }
    """
    # Generate a unique id for this user
    user_id = str(uuid.uuid4())

    user = User(
        event['customer_id'],
        user_id,
        name=event['name'],
    )
    user.save()
    return user.as_dict()

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
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError(f"User '{event['user_id']}' does not exist")
    return user.as_dict()

def update_user_handler(event, context):
    """Update details of a single user.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'name': 'Peter Gibbons',
    }
    """
    try:
        user = User.lookup(event['user_id'], event.get('customer_id'))
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError(f"User '{event['user_id']}' does not exist")

    user.name = event.get('name', user.name)
    user.save()
    return user.as_dict()

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
