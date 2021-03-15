import uuid

from pynamodb.attributes import UnicodeAttribute
import pynamodb.models

class Post(pynamodb.models.Model):
    class Meta:
        table_name = 'post'
        region = 'us-west-2'

    customer_id = UnicodeAttribute(hash_key=True)
    post_id = UnicodeAttribute(range_key=True)
    summary = UnicodeAttribute()
    description = UnicodeAttribute(null=True)

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
