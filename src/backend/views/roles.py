# AGAIN NEW CODE

from asyncio.windows_events import NULL
from datetime import datetime
from genericpath import exists
from optparse import Values
import re
from turtle import update
from venv import create

from backend.models import customer

from backend.common import permission
from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint
from sqlalchemy import select
from backend.common.exceptions import NotAllowedError
from backend.common.http import make_no_content_response
from backend.common.resume import Resume
from backend.models.db import transaction
from backend.models.language import Language
from backend.models.skill import Skill
from backend.models.customer import Customer
from backend.models.user import User, UserRole, UserRoleMapping
from backend.views.base import AuthenticatedAPIBase
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.models.notification import Notification
from backend.common.permission import Permissions
from backend.models.activities import Activity, ActivityGlobal, ActivityType
from sqlalchemy.orm import Session


blueprint = Blueprint('role', __name__, url_prefix='/roles')
role_insert_blueprint = Blueprint('role_insert', __name__, url_prefix='/user/roles')



@role_insert_blueprint.route('')
class RoleInsert(AuthenticatedAPIBase):
    @staticmethod
    def get():  # pylint: disable=too-many-locals
        payload = request.json
        print("--------hi----------akash-------------")
        with transaction() as tx:
            #user_ = User.lookup(tx, current_cognito_jwt['sub'])
            #print("=========",user_.id)
            users = tx.execute(select(User.id).where(User.customer_id == payload.get('customer_id'))).scalars().all()
            print("-=======........----------",users)
            #print("..........",UserRoleMapping.customer_id)
            return "okk 500 akash"

    @staticmethod
    def post():  # pylint: disable=too-many-locals
        payload = request.json
        now = datetime.utcnow()   
        with transaction() as tx:
            #user_ = User.lookup(tx, current_cognito_jwt['sub'])
            roles = UserRole(id=payload.get('id'), 
            customer_id=payload.get('customer_id'), role=payload.get('role'),
            permissions=payload.get('permissions'),
            created_at =now,
            last_updated_at=datetime.utcnow())
            tx.add(roles)
            #print("--------- add ---------------",roles.id)
            #if user_.customer_id == payload.get('customer_id'):    
            #print("----ok-----------1--")
            users = tx.execute(select(User.id).where(User.customer_id == payload.get('customer_id'))).scalars().first()
            #print("===========",roles.customer_id)
            #print(">>>>>>>>>>",users)
            if users != NULL:
                user_role_mappings = UserRoleMapping(id=payload.get('id'), user_id=users, 
                customer_id= roles.customer_id, user_role_id=roles.id,
                created_at =now,
                last_updated_at=datetime.utcnow())
                #print("----ok-----------2--")
                tx.add(user_role_mappings)
                #print("----ok----------3---")
                #print("--------- user id of user role mapping ---------------",user_role_mappings.user_id)
                return "inserted dada okk"


    @staticmethod
    def put():  # pylint: disable=too-many-locals
        payload = request.json
        now = datetime.utcnow()   
        with transaction() as tx:
            users_roles = tx.execute(select(UserRole).where(UserRole.id == payload.get('id') and UserRole.cutomer_id == payload.get('customer_id'))).scalars().first()
            #print("***** user_role is ******",users_roles.id)
            #print("---------customer id --------",users_roles.customer_id)
            role_id=payload.get('id')
            if role_id == users_roles.id:
                #print("-----------okkk-----------",role_id)
                user_query = tx.query(UserRole).filter_by(id=role_id)
                data_to_update = dict(role=payload.get('role'), permissions= payload.get('permissions'), last_updated_at=now)
                user_query.update(data_to_update)
                return "successfully updated"








    # @staticmethod
    # def put():  # pylint: disable=too-many-locals
    #     payload = request.json
    #     now = datetime.utcnow()   
    #     with transaction() as tx:
    #         users_roles = tx.execute(select(UserRole).where(UserRole.id == payload.get('id'))).scalars().first()
    #         print("***********",users_roles.id)
    #         print("-----------------",users_roles.customer_id)
    #         role_id=payload.get('id')
    #         if role_id == users_roles.id:
    #             print("-----------okkk-----------",role_id)
    #             #exit(0)
    #             #roles_name = payload.get('role')
    #             #print("99999999===========",roles)
    #             #roles=(UserRole(customer_id=payload.get('customer_id'),role=payload.get('role'), permissions=payload.get('permissions'), last_updated_at=datetime.utcnow()))
    #             #UserRole.permissions=payload.get('permissions'),
    #             #UserRole.last_updated_at=datetime.utcnow()
    #             #print("+++++++++++++",roles.permissions)
    #             #role = UserRole(customer_id=roles.customer_id, role=roles.role, permissions=roles.permissions, last_upated_at=roles.last_upated_at)
    #             #role = UserRole(role=roles.role)
    #             # if payload.get('role'):
    #             #     UserRole.role = payload.get('role')

    #             # if payload.get('permissions'):
    #             #     UserRole.permissions = payload.get('permissions')
                    
    #             # roles = UserRole(#id=payload.get('id'), customer_id=payload.get('customer_id'), 
    #             # role=payload.get('role'),
    #             # permissions=payload.get('permissions'),
    #             # #created_at =now,
    #             # last_updated_at=datetime.utcnow())
    #             user_query = tx.query(UserRole).filter_by(id=role_id)
    #             data_to_update = dict(role=payload.get('role'), permissions= payload.get('permissions'))
    #             user_query.update(data_to_update)

    #             #tx.add(roles)
    #             #tx.session.query(UserRole).filter(UserRole.id == role_id).update(UserRole.role: roles_name, synchronize_session = False)
    #             #setattr()

    #             # print("++++++ 1 +++++++",roles.permissions)
    #             # print("++++++++ 2 +++++",roles.customer_id)
    #             # print("+++++++++ 3 ++++",roles.last_updated_at)
    #             # print("++++  4 +++++++++",roles.role)
    #             #tx.add(roles)
    #             print("66666666666666")
    #             return "okkk"


    # @staticmethod
    # def put():  # pylint: disable=too-many-locals
    #     payload = request.json
    #     now = datetime.utcnow()   
    #     with transaction() as tx:
    #         #user_ = User.lookup(tx, current_cognito_jwt['sub'])
    #         role_id=payload.get('id')
    #         customer_id=payload.get('customer_id')
    #         role_name=payload.get('role')
    #         role_permissions=payload.get('permissions')
    #         users_roles=tx.execute(select(UserRole).where(UserRole.id == role_id)).scalars().first()
    #         print("--------1---------",users_roles)
    #         print("---------2--------",users_roles.id)
    #         print("---------3--------",users_roles.customer_id)
    #         print("---------4--------",users_roles.role)
    #         print("---------5--------",users_roles.permissions)
    #         print("---------6--------",role_id)
    #         print("---------7--------",role_name)
    #         print("---------8--------",role_permissions)
    #         # roles_update=UserRole(
    #         #         role=role_name,
    #         #         customer_id=customer_id,
    #         #         permissions=role_permissions,
    #         #         #created_at=now,
    #         #         last_updated_at=datetime.utcnow())
    #         # tx.add(roles_update)
    #         # return "okkkk"
    #         if role_id == users_roles.id:
    #             print("*************")
    #             if customer_id == users_roles.customer_id:
    #                 print("................................... olllaaa ............................")
    #                 roles = UserRole(customer_id=customer_id,
    #                                 role=role_name,
    #                                 permissions=role_permissions,
    #                                 #created_at=now,
    #                                 last_updated_at=datetime.utcnow())
    #                 tx.execute(roles)
    #                 return "okkkk"
    #         return "Not okkk"

    #         #     customer_id = users.customer_id 
    #         #     roles = UserRole(id=role_id, 
    #         #     customer_id=customer_id, role=payload.get('role'),
    #         #     permissions=payload.get('permissions'),
    #         #     last_updated_at=datetime.utcnow())
    #         #     print("--------------ohhhhhhh---------------")
    #         #     tx.add(roles)
    #         #return "User Updated Succesfully"