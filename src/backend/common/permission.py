from sqlalchemy import select
from backend.models.user import UserRole, UserRoleMapping


class Permissions:  # pylint: disable=too-few-public-methods
    @staticmethod
    def get_user_role(tx, user_id):
        current_user_role = tx.execute(
            select(UserRole).where(
                UserRole.id == UserRoleMapping.user_role_id and UserRoleMapping.user_id == user_id
            )
        ).scalars().first()
        return current_user_role

    @staticmethod
    def check_user_permission(customer_id, user_customer_id):
        if customer_id == user_customer_id:
            return True
        else:
            False
