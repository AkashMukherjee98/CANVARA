"""AWS Lambda functions related to customers"""

import uuid

import pynamodb.exceptions
from base import registered_operations_handler
from common.decorators import register
from common.exceptions import DoesNotExistError, InvalidOperationError
from models.customer import Customer

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

    # Generate a unique id for this customer
    customer_id = str(uuid.uuid4())

    customer = Customer(
        customer_id,
        name=event['name'],
    )
    customer.save()
    return customer.as_dict()

@register(OPERATIONS_REGISTRY, 'list_customers')
def list_customers_handler(event, context):
    """Return all customers."""
    customers = [customer.as_dict() for customer in Customer.scan()]
    return customers

@register(OPERATIONS_REGISTRY, 'get_customer')
def get_customer_handler(event, context):
    """Return details of a single customer.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
    }
    """
    try:
        customer = Customer.get(event['customer_id'])
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Customer does not exist")
    return customer.as_dict()

@register(OPERATIONS_REGISTRY, 'update_customer')
def update_customer_handler(event, context):
    """Update details of a single customer.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
        'name': 'Updated name goes here',
    }
    """
    try:
        customer = Customer.get(event['customer_id'])
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Customer does not exist")

    customer.name = event.get('name', customer.name)
    customer.save()
    return customer.as_dict()

@register(OPERATIONS_REGISTRY, 'delete_customer')
def delete_customer_handler(event, context):
    """Delete a single customer.

    Sample payload:
    {
        'customer_id': 'c9028558-e464-44ba-ab8d-bc8e37f4f7d1',
    }
    """
    try:
        customer = Customer.get(event['customer_id'])
    except pynamodb.exceptions.DoesNotExist:
        # Noop if the customer does not exist
        return
    customer.delete()
