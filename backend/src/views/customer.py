import uuid

from flask import jsonify, request
from flask_cognito import cognito_auth_required
import pynamodb.exceptions

from app import app
from common.exceptions import DoesNotExistError
from models.customer import Customer

@app.route('/customers', methods=['POST'])
@cognito_auth_required
def create_customer_handler():
    # Generate a unique id for this customer
    customer_id = str(uuid.uuid4())

    customer = Customer(
        customer_id,
        name=request.json['name'],
    )
    customer.save()
    return customer.as_dict()

@app.route('/customers')
@cognito_auth_required
def list_customers_handler():
    customers = [customer.as_dict() for customer in Customer.scan()]
    return jsonify(customers)

@app.route('/customers/<customer_id>')
@cognito_auth_required
def get_customer_handler(customer_id):
    try:
        customer = Customer.get(customer_id)
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Customer does not exist")
    return customer.as_dict()

@app.route('/customers/<customer_id>', methods=['PUT'])
@cognito_auth_required
def update_customer_handler(customer_id):
    try:
        customer = Customer.get(customer_id)
    except pynamodb.exceptions.DoesNotExist:
        raise DoesNotExistError("Customer does not exist")

    customer.name = request.json.get('name', customer.name)
    customer.save()
    return customer.as_dict()

@app.route('/customers/<customer_id>', methods=['DELETE'])
@cognito_auth_required
def delete_customer_handler(customer_id):
    try:
        customer = Customer.get(customer_id)
    except pynamodb.exceptions.DoesNotExist:
        # Noop if the customer does not exist
        return {}
    customer.delete()
    return {}
