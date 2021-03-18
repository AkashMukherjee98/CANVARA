"""AWS Lambda functions related to posts"""

import uuid

from models.post import Post

def create_post_handler(event, context):
    """Handler for create_post Lambda function

    Sample payload:
    {
        'customer_id': '1234'
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

    return {
        'statusCode': 200,
    }

def list_posts_handler(event, context):
    """Handler for list_posts Lambda function

    Sample payload:
    {
        'customer_id': '1234'
    }
    """

    posts = [post.as_dict() for post in Post.query(event['customer_id'])]

    return {
        'statusCode': 200,
        'posts': posts
    }
