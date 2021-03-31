from pynamodb.attributes import UnicodeAttribute
import pynamodb.models

class Customer(pynamodb.models.Model):
    class Meta:
        table_name = 'customer'
        region = 'us-west-2'

    customer_id = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()

    def as_dict(self):
        return {
            'customer_id': self.customer_id,
            'name': self.name,
        }
