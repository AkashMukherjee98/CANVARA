"""AWS Lambda functions related to posts"""

import uuid

import pynamodb.exceptions
from models.post import Post

class DoesNotExistError(Exception):
    """Raised when a request entity is not found"""

def create_post_handler(event, context):
    """Handler for create_post Lambda function

    Sample payload:
    {
        'customer_id': '1234',
        'post': {
            'summary': 'Task summary goes here',
            'description': 'Additional details go here'
        }
    }
    """
    post_data = event['post']

    # Generate a unique id for this post
    post_id = str(uuid.uuid4())

    post = Post(
        event['customer_id'],
        post_id,
        summary=post_data['summary'],
        description=post_data['description']
    )
    post.save()
    return post.as_dict()

def list_posts_handler(event, context):
    """Handler for list_posts Lambda function

    Sample payload:
    {
        'customer_id': '1234'
    }
    """

    posts = [post.as_dict() for post in Post.query(event['customer_id'])]
    return posts

def get_post_handler(event, context):
    """Handler for get_post Lambda function

    Sample payload:
    {
        'customer_id': '1234',
        'post_id': 'abcd5678'
    }
    """
    try:
        post = Post.get(event['customer_id'], event['post_id'])
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Post does not exist")
    return post.as_dict()

def update_post_handler(event, context):
    """Handler for update_post Lambda function

    Sample payload:
    {
        'customer_id': '1234',
        'post': {
            'post_id': 'abcd5678',
            'summary': 'Updated task summary goes here',
            'description': 'Updated details go here'
        }
    }
    """
    post_data = event['post']

    try:
        post = Post.get(event['customer_id'], post_data['post_id'])
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Post does not exist")

    post.summary = post_data.get('summary', post.summary)
    post.description = post_data.get('description', post.description)
    post.save()
    return post.as_dict()

def delete_post_handler(event, context):
    """Handler for delete_post Lambda function

    Sample payload:
    {
        'customer_id': '1234',
        'post_id': 'abcd5678'
    }
    """
    try:
        post = Post.get(event['customer_id'], event['post_id'])
    except pynamodb.exceptions.DoesNotExist:
        # Noop if the post does not exist
        return
    post.delete()
