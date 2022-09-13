from faulthandler import is_enabled
from itertools import product
from turtle import update
import uuid

from flask import jsonify, request
from flask_smorest import Blueprint

from sqlalchemy import select


from backend.common.exceptions import DoesNotExistError
from backend.common.http import make_no_content_response
from backend.models.customer import Customer
from backend.models.db import transaction
from backend.views.base import AuthenticatedAPIBase
#from backend.models.assignment.AssignmentApplication

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
            products_enabled=request.json['products_enabled']
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

    # @staticmethod
    # def put(customer_id):
    #     with transaction() as tx:
    #         customer = Customer.lookup(tx, customer_id)
    #         customer.name = request.json.get('name', customer.name)
    #         customer.products_enabled = request.json.get('products_enabled', customer.products_enabled)
    #     return customer.as_dict()

    @staticmethod
    def put(customer_id):
        with transaction() as tx:
            customer = Customer.lookup(tx, customer_id)
            payload = request.json
            data=customer.products_enabled
            # data=[payload["products_enabled"][0] if x.get("artifact_name")==payload["products_enabled"][0]["artifact_name"] else x for x in data]
            # print("----------data--------",data)
            # print("---------payload---------",payload)
            # customer.products_enabled = data
            # return customer.as_dict()

            data=[payload["products_enabled"][0] if x.get("artifact_name")==payload["products_enabled"][0]["artifact_name"] else x for x in data]
            customer.products_enabled = data
            if payload["products_enabled"][0] not in customer.products_enabled:                
                c_data=customer.products_enabled
                c_data.append(payload["products_enabled"][0])
                customer.products_enabled = c_data
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





















            # for x in data:
            #     if x.get("artifact_name")==payload["products_enabled"][0]["artifact_name"]:
            #         x.update(payload["products_enabled"][0])
            #         # customer.products_enabled = data
            #         # return customer.as_dict()
            # customer.products_enabled = data
            # #print("---- customer data -------",customer.products_enabled)
            # return customer.as_dict()
            
            
            
            # # if payload["products_enabled"]["artifact_name"] == 'Offer':
            #     data[0].update(payload["products_enabled"])
            # print("okkkk   ",data)

            # for i in payload.get('products_enabled'):
            #     print("for i data ",i)
            #     for j in customer.products_enabled:
            #         print("for j data",j)
            #         if i['artifact_name'] == j["artifact_name"]:
            #         #customer.get('products_enabled') = payload.get('products_enabled')['is_enabled']
            #             #customer.products_enabled = j["is_enabled"]
            #             print("--- i --",i["artifact_name"])
            #             print("--- j --",j["artifact_name"])
            #             data.update(value)
            #             print("-------",data)
            #             #customer.products_enabled = payload.get('products_enabled')
            #             return customer.as_dict()

            # json_data =[]
            # product_data=[]
            
            # products =payload.get('products_enabled')

            # for products in payload.get('products_enabled'):
            #     #print("---- 123 -----",products)
            #     json_data.append(products)
            # print("---- postman  -----",json_data)
            # for customers in customer.products_enabled:
            #     #print("-------- customer product enabled ------",customers)
            #     product_data.append(customers)
            # print("-- database -----",product_data)
            # for i in product_data:
            #     for j in json_data:
            #         if i.get('artifact_name')==j.get('artifact_name'):
            #             i["is_enabled"]=j['is_enabled']
            #             print(i)
            #             print("ok")

            
            
    
            #exit(0)
                #    if i["artifact_name"] == j["artifact_name"]:
                #        print(" ....... ok ....... ")
                        #product_data.update(json_data)
                        #print(" ok ",product_data)

                    

                    
                #print("------- j ---------",j)
                    # if customers["artifact_name"] == products["artifact_name"]:
                    #     print(" from json ",products)
                    #     print(" from table ",customers)
                    #     Dictionary1 = {'is_enabled': customers["is_enabled"], 'artifact_name': customers["artifact_name"]}
                    #     Dictionary2 = {'is_enabled': products["is_enabled"], 'artifact_name': products["artifact_name"] }
                    #     Dictionary1.update(Dictionary2)
                    #     print("Dictionary after updation:")
                    #     print("----- after updation ------------",Dictionary1)
                    #     # dic.update(is_enabled=products["is_enabled"])
                    #     #customers = tx.query(Customer).filter_by(id=customer_id)
                    #     #data_to_update = dict(is_enabled=products["is_enabled"])
                    #     # data_to_update =  j.update(products["is_enabled"])
                    #     #customer_query = tx.query(Customer).filter_by(id=customer_id)
                    #     #customer_query.update(dict(Dictionary1))
                    #     customer.update(dict(Dictionary1))
                    #     return customer.as_dict()
                    # else:
                    #     print("not solve")
                # #customer_query = tx.execute(select(Customer).where(id == customer_id)).scalars().all()
                # #return jsonify([customers.as_dict() for customers in customer_query])
                # exit(0)

            # for i in customer.products_enabled:
            #     print("-------- artifact name -----------",i)
            #     if i["artifact_name"] == 'Offer':
            #         print("-- name ---",i["is_enabled"])
            #         return customer.as_dict()
            #         # user_query = tx.query(Customer).filter_by(id=customer_id)
            #         #data_to_update = i["is_enabled"]
            #         #customer.update(data_to_update)
            #     else:
            #         print("Error")
            # exit(0)
        

    # @staticmethod
    # def delete(customer_id):
    #     with transaction() as tx:
    #         customer = Customer.lookup(tx, customer_id)
    #         # if customer does not exist, error code 404 is displayed
    #         if customer is None:
    #             raise DoesNotExistError("404 Error, Customer Does Not Exist")
    #         # delete customer
    #         tx.delete(customer)
    #     return make_no_content_response()
