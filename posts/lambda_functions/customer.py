"""AWS Lambda functions related to customers"""

import uuid

import pynamodb.exceptions
from common.exceptions import DoesNotExistError
from models.customer import Customer

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

def list_customers_handler(event, context):
    """Return all customers."""
    customers = [customer.as_dict() for customer in Customer.scan()]
    return customers

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
