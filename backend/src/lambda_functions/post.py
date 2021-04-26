"""AWS Lambda functions related to posts"""

from datetime import datetime
import uuid

from common.exceptions import DoesNotExistError, NotAllowedError
from models.post import Post
from models.user import User

def create_post_handler(event, context):
    """Create a new post.

    Sample payload:
    {
        'post_owner_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'task_owner_id': '085d75d2-5b84-412e-aad4-7262977a327a',
        'summary': 'Task summary goes here',
        'description': 'Additional details go here'
    }
    """
    post_owner_id = event['post_owner_id']
    post_owner = User.lookup(post_owner_id)

    # Validate the task_owner_id, if it was specified
    task_owner_id = event.get('task_owner_id', post_owner_id)
    if task_owner_id != post_owner_id and not User.exists(task_owner_id):
        raise DoesNotExistError(f"User '{task_owner_id}' does not exist")

    # Generate a unique id for this post
    post_id = str(uuid.uuid4())

    now = datetime.utcnow().isoformat()
    post = Post(
        post_owner.customer_id,
        post_id,
        post_owner_id=post_owner_id,
        task_owner_id=task_owner_id,
        summary=event['summary'],
        description=event['description'],
        created_at=now,
        last_updated_at=now
    )
    post.save()
    return post.as_dict()

def list_posts_handler(event, context):
    """Return all posts based on given criteria.

    Sample payload:
    {
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'post_owner_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'task_owner_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'query': 'some text'
    }
    """
    # This is the user making the request, for authorization purposes
    user = User.lookup(event['user_id'])

    return Post.search(
        user.customer_id,
        post_owner_id=event.get('post_owner_id'),
        task_owner_id=event.get('task_owner_id'),
        query=event.get('query')
        )

def get_post_handler(event, context):
    """Get details of a single post.

    Sample payload:
    {
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'post_id': '1f5aac8b-5b52-4aaa-af02-e677f6edb54c'
    }
    """
    user = User.lookup(event['user_id'])
    post = Post.lookup(user.customer_id, event['post_id'])
    return post.as_dict()

def update_post_handler(event, context):
    """Update details of a single post.

    Sample payload:
    {
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'post_id': '1f5aac8b-5b52-4aaa-af02-e677f6edb54c',
        'task_owner_id': '085d75d2-5b84-412e-aad4-7262977a327a',
        'summary': 'Updated task summary goes here',
        'description': 'Updated details go here'
    }
    """
    user = User.lookup(event['user_id'])
    post = Post.lookup(user.customer_id, event['post_id'])

    # For now, only the post owner is allowed to update the post
    if post.post_owner_id != event['user_id']:
        raise NotAllowedError(f"User '{event['user_id']}' is not the post owner")

    # Validate the task_owner_id, if it was specified
    task_owner_id = event.get('task_owner_id', post.task_owner_id)
    if task_owner_id != post.task_owner_id and not User.exists(task_owner_id):
        raise DoesNotExistError(f"User '{task_owner_id}' does not exist")

    post.task_owner_id = task_owner_id
    post.summary = event.get('summary', post.summary)
    post.description = event.get('description', post.description)
    post.last_updated_at = datetime.utcnow().isoformat()
    post.save()
    return post.as_dict()

def delete_post_handler(event, context):
    """Delete a single post.

    Sample payload:
    {
        'user_id': '1cfa6354-580e-464e-b350-74d2c7b7793b',
        'post_id': '1f5aac8b-5b52-4aaa-af02-e677f6edb54c'
    }
    """
    user = User.lookup(event['user_id'])
    post = Post.lookup(user.customer_id, event['post_id'], must_exist=False)

    if post is None:
        # Noop if the post does not exist
        return

    # For now, only the post owner is allowed to delete the post
    if post.post_owner_id != event['user_id']:
        raise NotAllowedError(f"User '{event['user_id']}' is not the post owner")

    post.delete()
