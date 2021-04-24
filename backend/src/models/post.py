from pynamodb.attributes import UnicodeAttribute
from pynamodb.expressions.condition import Condition
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
import pynamodb.models
import pynamodb.exceptions
from common.exceptions import DoesNotExistError

class PostOwnerIdIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'post_owner_id-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    customer_id = UnicodeAttribute(hash_key=True)
    post_owner_id = UnicodeAttribute(range_key=True)

class TaskOwnerIdIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'task_owner_id-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    customer_id = UnicodeAttribute(hash_key=True)
    task_owner_id = UnicodeAttribute(range_key=True)

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
    task_owner_id_index = TaskOwnerIdIndex()

    @classmethod
    def lookup(cls, customer_id, post_id, must_exist=True):
        try:
            return Post.get(customer_id, post_id)
        except pynamodb.exceptions.DoesNotExist:
            if must_exist:
                raise DoesNotExistError(f"Post '{post_id}' does not exist")
        return None

    @classmethod
    def search(cls, customer_id, post_owner_id=None, task_owner_id=None, query=None):
        posts = []
        index_name = None
        filter_condition = None

        if post_owner_id is not None:
            index_name = Post.post_owner_id_index.Meta.index_name
            filter_condition &= (Post.task_owner_id == post_owner_id)

        if task_owner_id is not None:
            index_name = Post.task_owner_id_index.Meta.index_name
            filter_condition &= (Post.task_owner_id == task_owner_id)

        if query is not None:
            filter_condition &= (Post.summary.contains(query) | Post.description.contains(query))

        posts = Post.query(customer_id, filter_condition=filter_condition, index_name=index_name)
        return [post.as_dict() for post in posts]

    def as_dict(self):
        return {
            'customer_id': self.customer_id,
            'post_id': self.post_id,
            'post_owner_id': self.post_owner_id,
            'task_owner_id': self.task_owner_id,
            'summary': self.summary,
            'description': self.description,
        }
