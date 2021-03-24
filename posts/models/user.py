from pynamodb.attributes import UnicodeAttribute
import pynamodb.models

class User(pynamodb.models.Model):
    class Meta:
        table_name = 'user'
        region = 'us-west-2'

    customer_id = UnicodeAttribute(hash_key=True)
    user_id = UnicodeAttribute(range_key=True)
    name = UnicodeAttribute()

    @classmethod
    def lookup(cls, user_id, customer_id=None):
        if customer_id is None:
            # TODO: (sunil) Not Yet Implemented
            raise NotImplementedError()
        return User.get(customer_id, user_id)

    def as_dict(self):
        return {
            'customer_id': self.customer_id,
            'user_id': self.user_id,
            'name': self.name,
        }
