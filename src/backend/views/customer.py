import uuid

from flask import jsonify, request
from flask.views import MethodView

from sqlalchemy import select

from backend.models.customer import Customer
from backend.models.db import transaction


class CustomerAPI(MethodView):
    @staticmethod
    def __list_customers():
        with transaction() as tx:
            customers = tx.execute(select(Customer)).scalars().all()
        return jsonify([customer.as_dict() for customer in customers])

    @staticmethod
    def __get_customer(customer_id):
        with transaction() as tx:
            customer = Customer.lookup(tx, customer_id)
        return customer.as_dict()

    @staticmethod
    def get(customer_id=None):
        if customer_id is None:
            return CustomerAPI.__list_customers()
        return CustomerAPI.__get_customer(customer_id)

    @staticmethod
    def post():
        # Generate a unique id for this customer
        customer_id = str(uuid.uuid4())

        customer = Customer(
            id=customer_id,
            name=request.json['name'],
        )

        with transaction() as tx:
            tx.add(customer)
        return customer.as_dict()

    @staticmethod
    def put(customer_id):
        with transaction() as tx:
            customer = Customer.lookup(tx, customer_id)
            customer.name = request.json.get('name', customer.name)
        return customer.as_dict()

    @staticmethod
    def delete(customer_id):
        with transaction() as tx:
            customer = Customer.lookup(tx, customer_id, must_exist=False)
            if customer is None:
                # Noop if the customer does not exist
                return {}
            tx.delete(customer)
        return {}
