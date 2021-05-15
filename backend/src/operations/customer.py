import uuid

import pynamodb.exceptions
from common.exceptions import DoesNotExistError
from models.customer import Customer

def create_customer(name):
    """Create a new customer."""

    # Generate a unique id for this customer
    customer_id = str(uuid.uuid4())

    customer = Customer(customer_id, name=name)
    customer.save()
    return customer.as_dict()

def list_all_customers():
    """Return all customers."""
    customers = [customer.as_dict() for customer in Customer.scan()]
    return customers

def get_customer(customer_id):
    """Return details of a single customer."""
    try:
        customer = Customer.get(customer_id)
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Customer does not exist")
    return customer.as_dict()

def update_customer(customer_id, name=None):
    """Update details of a single customer."""
    try:
        customer = Customer.get(customer_id)
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Customer does not exist")

    if name is not None:
        customer.name = name
    customer.save()
    return customer.as_dict()

def delete_customer(customer_id):
    """Delete a single customer."""
    try:
        customer = Customer.get(customer_id)
    except pynamodb.exceptions.DoesNotExist:
        # Noop if the customer does not exist
        return
    customer.delete()
