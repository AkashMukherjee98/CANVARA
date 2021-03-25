from pynamodb.attributes import UnicodeAttribute
import pynamodb.models

class Post(pynamodb.models.Model):
    class Meta:
        table_name = 'post'
        region = 'us-west-2'

    customer_id = UnicodeAttribute(hash_key=True)
    post_id = UnicodeAttribute(range_key=True)
    post_owner_id = UnicodeAttribute()
    task_owner_id = UnicodeAttribute()
    summary = UnicodeAttribute()
    description = UnicodeAttribute(null=True)

    def as_dict(self):
        return {
            'customer_id': self.customer_id,
            'post_id': self.post_id,
            'post_owner_id': self.post_owner_id,
            'task_owner_id': self.task_owner_id,
            'summary': self.summary,
            'description': self.description,
        }
