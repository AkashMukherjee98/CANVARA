import uuid

from flask import current_app as app
from flask import jsonify, request
from flask_cognito import cognito_auth_required

from sqlalchemy import select

from backend.models.customer import Customer
from backend.models.db import transaction


@app.route('/customers', methods=['POST'])
@cognito_auth_required
def create_customer_handler():
    # Generate a unique id for this customer
    customer_id = str(uuid.uuid4())

    customer = Customer(
        id=customer_id,
        name=request.json['name'],
    )

    with transaction() as tx:
        tx.add(customer)
    return customer.as_dict()


@app.route('/customers')
@cognito_auth_required
def list_customers_handler():
    with transaction() as tx:
        customers = tx.execute(select(Customer)).scalars().all()
    return jsonify([customer.as_dict() for customer in customers])


@app.route('/customers/<customer_id>')
@cognito_auth_required
def get_customer_handler(customer_id):
    with transaction() as tx:
        customer = Customer.lookup(tx, customer_id)
    return customer.as_dict()


@app.route('/customers/<customer_id>', methods=['PUT'])
@cognito_auth_required
def update_customer_handler(customer_id):
    with transaction() as tx:
        customer = Customer.lookup(tx, customer_id)
        customer.name = request.json.get('name', customer.name)
    return customer.as_dict()


@app.route('/customers/<customer_id>', methods=['DELETE'])
@cognito_auth_required
def delete_customer_handler(customer_id):
    with transaction() as tx:
        customer = Customer.lookup(tx, customer_id, must_exist=False)
        if customer is None:
            # Noop if the customer does not exist
            return {}
        tx.delete(customer)
    return {}
