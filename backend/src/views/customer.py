"""Views related to customers"""

from flask import jsonify, request
from flask_cognito import cognito_auth_required

from app import app
from operations import customer

@app.route('/customers', methods=['POST'])
@cognito_auth_required
def create_customer_handler():
    return customer.create_customer(request.json['name'])

@app.route('/customers')
@cognito_auth_required
def list_customers_handler():
    return jsonify(customer.list_all_customers())

@app.route('/customers/<customer_id>')
@cognito_auth_required
def get_customer_handler(customer_id):
    return customer.get_customer(customer_id)

@app.route('/customers/<customer_id>', methods=['PUT'])
@cognito_auth_required
def update_customer_handler(customer_id):
    return customer.update_customer(customer_id, request.json.get('name'))

@app.route('/customers/<customer_id>', methods=['DELETE'])
@cognito_auth_required
def delete_customer_handler(customer_id):
    customer.delete_customer(customer_id)
    return {}