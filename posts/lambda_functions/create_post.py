import uuid

from models.post import Post

def lambda_handler(event, context):
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
