from models.post import Post

def lambda_handler(event, context):
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
