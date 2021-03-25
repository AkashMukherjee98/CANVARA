"""AWS Lambda functions related to posts"""

import uuid

import pynamodb.exceptions
from common.exceptions import DoesNotExistError
from models.post import Post

def create_post_handler(event, context):
    """Create a new post.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'post_owner_id': '1cfa6354-580e-464e-b350-74d2c7b7793b'
        'task_owner_id': '085d75d2-5b84-412e-aad4-7262977a327a',
        'summary': 'Task summary goes here',
        'description': 'Additional details go here'
    }
    """
    # TODO: (sunil) lookup post_owner_id and task_owner_id to make sure those are valid users within this customer

    # Generate a unique id for this post
    post_id = str(uuid.uuid4())

    post = Post(
        event['customer_id'],
        post_id,
        post_owner_id=event['post_owner_id'],
        task_owner_id=event.get('task_owner_id', event['post_owner_id']),
        summary=event['summary'],
        description=event['description']
    )
    post.save()
    return post.as_dict()

def list_posts_handler(event, context):
    """Return all posts for a single customer.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
    }
    """

    # TODO: (sunil) accept post_owner_id and task_owner_id and filter on those
    posts = [post.as_dict() for post in Post.query(event['customer_id'])]
    return posts

def get_post_handler(event, context):
    """Get details of a single post.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'post_id': '1f5aac8b-5b52-4aaa-af02-e677f6edb54c'
    }
    """
    try:
        post = Post.get(event['customer_id'], event['post_id'])
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Post does not exist")
    return post.as_dict()

def update_post_handler(event, context):
    """Update details of a single post.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'post_id': '1f5aac8b-5b52-4aaa-af02-e677f6edb54c',
        'task_owner_id': '085d75d2-5b84-412e-aad4-7262977a327a',
        'summary': 'Updated task summary goes here',
        'description': 'Updated details go here'
    }
    """
    try:
        post = Post.get(event['customer_id'], event['post_id'])
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Post does not exist")

    # TODO: (sunil) lookup task_owner_id to make sure it is a valid user within this customer

    post.task_owner_id = event.get('task_owner_id', post.task_owner_id)
    post.summary = event.get('summary', post.summary)
    post.description = event.get('description', post.description)
    post.save()
    return post.as_dict()

def delete_post_handler(event, context):
    """Delete a single post.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'post_id': '1f5aac8b-5b52-4aaa-af02-e677f6edb54c'
    }
    """
    try:
        post = Post.get(event['customer_id'], event['post_id'])
    except pynamodb.exceptions.DoesNotExist:
        # Noop if the post does not exist
        return
    post.delete()
