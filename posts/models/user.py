from pynamodb.attributes import UnicodeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
import pynamodb.models
from common.exceptions import DoesNotExistError

class UserIdIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'user_id-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    user_id = UnicodeAttribute(hash_key=True)

class User(pynamodb.models.Model):
    class Meta:
        table_name = 'user'
        region = 'us-west-2'

    customer_id = UnicodeAttribute(hash_key=True)
    user_id = UnicodeAttribute(range_key=True)
    name = UnicodeAttribute()
    user_id_index = UserIdIndex()

    @classmethod
    def lookup(cls, user_id, customer_id=None):
        if customer_id is None:
            try:
                return next(User.user_id_index.query(user_id))
            except StopIteration:
                raise DoesNotExistError(f"User '{user_id}' does not exist")
        return User.get(customer_id, user_id)

    @classmethod
    def exists(cls, user_id, customer_id=None):
        if customer_id is None:
            return User.user_id_index.count(user_id) > 0
        return User.count(customer_id, user_id) > 0

    def as_dict(self):
        return {
            'customer_id': self.customer_id,
            'user_id': self.user_id,
            'name': self.name,
        }
