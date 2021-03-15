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
