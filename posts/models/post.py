from pynamodb.attributes import UnicodeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
import pynamodb.exceptions
import pynamodb.models
from common.exceptions import DoesNotExistError

class PostOwnerIdIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'post_owner_id-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    customer_id = UnicodeAttribute(hash_key=True)
    post_owner_id = UnicodeAttribute(range_key=True)

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

    # Secondary Indexes
    post_owner_id_index = PostOwnerIdIndex()

    @classmethod
    def lookup(cls, customer_id, post_id, must_exist=True):
        try:
            return Post.get(customer_id, post_id)
        except pynamodb.exceptions.DoesNotExist:
            if must_exist:
                raise DoesNotExistError(f"Post '{post_id}' does not exist")
        return None

    def as_dict(self):
        return {
            'customer_id': self.customer_id,
            'post_id': self.post_id,
            'post_owner_id': self.post_owner_id,
            'task_owner_id': self.task_owner_id,
            'summary': self.summary,
            'description': self.description,
        }
