import uuid

from flask import jsonify, request
from flask_smorest import Blueprint

from sqlalchemy import select


from backend.common.exceptions import DoesNotExistError
from backend.common.http import make_no_content_response
from backend.models.customer import Customer
from backend.models.db import transaction
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('customer', __name__, url_prefix='/customers')


@blueprint.route('')
class CustomerAPI(AuthenticatedAPIBase):

    @staticmethod
    def get():
        with transaction() as tx:
            customers = tx.execute(select(Customer)).scalars().all()
        return jsonify([customer.as_dict() for customer in customers])

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


@blueprint.route('/<customer_id>')
class CustomerByIdAPI(AuthenticatedAPIBase):

    @staticmethod
    def get(customer_id):
        with transaction() as tx:
            customer = Customer.lookup(tx, customer_id)
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
            # delete customer
            tx.delete(customer)
        return make_no_content_response()
