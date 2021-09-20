import uuid

from flask import jsonify, request

from sqlalchemy import select

from backend.common.exceptions import DoesNotExistError
from backend.models.customer import Customer
from backend.models.db import transaction
from backend.views.base import AuthenticatedAPIBase
from Tools.scripts.patchcheck import status
from pip._internal.cli import status_codes
from logging import __status__


class CustomerAPI(AuthenticatedAPIBase):

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

            customer = Customer.lookup(tx, customer_id)
            # if customer does not exist, error code 404 is displayed
            if customer is None:
                raise DoesNotExistError("404 Error, Customer Does Not Exist")
            else:
                # delete customer 
                tx.delete(customer)            

            customer = Customer.lookup(tx, customer_id, must_exist=False)
            # if customer does not exist, error code 404 is displayed
            if customer is None:
                raise NotAllowedError("404 Error, Customer Does Not Exist")
            else:
                # delete customer 
                tx.delete(customer)
                # return deleted status code, empty response
                customer.status = Customer.DELETED.value 
            

        return make_no_content_response()
