"""AWS Lambda functions related to customers"""

from base import registered_operations_handler
from common.decorators import register
from operations import customer

OPERATIONS_REGISTRY = {}

def customer_operations_handler(event, context):
    """Handle customer-related operations"""
    return registered_operations_handler(OPERATIONS_REGISTRY, event, context)

@register(OPERATIONS_REGISTRY, 'create_customer')
def create_customer_handler(event, context):
    """Create a new customer.

    Sample payload:
    {
        'name': 'Initech Corporation'
    }
    """
    return customer.create_customer(event['name'])

@register(OPERATIONS_REGISTRY, 'list_customers')
def list_customers_handler(event, context):
    """Return all customers."""
    return customer.list_all_customers()

@register(OPERATIONS_REGISTRY, 'get_customer')
def get_customer_handler(event, context):
    """Return details of a single customer.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
    }
    """
    return customer.get_customer(event['customer_id'])

@register(OPERATIONS_REGISTRY, 'update_customer')
def update_customer_handler(event, context):
    """Update details of a single customer."""
    return customer.update_customer(event['customer_id'], event.get('name'))

@register(OPERATIONS_REGISTRY, 'delete_customer')
def delete_customer_handler(event, context):
    """Delete a single customer.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
    }
    """
    customer.delete_customer(event['customer_id'])
