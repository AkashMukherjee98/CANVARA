"""create and populate product_preference tables

Revision ID: e63d316c4e6e
Revises: abc8da851630
Create Date: 2021-06-14 12:21:19.573593

"""
import uuid

from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.schema import ForeignKey
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e63d316c4e6e'
down_revision = 'abc8da851630'
branch_labels = None
depends_on = None


def upgrade():
    product_preference_table = op.create_table(
        'product_preference',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
    )

    op.bulk_insert(
        product_preference_table,
        [
            {'id': str(uuid.uuid4()), 'name': 'Find help with my projects'},
            {'id': str(uuid.uuid4()), 'name': 'Opportunities to contribute'},
            {'id': str(uuid.uuid4()), 'name': 'Grow my skills'},
            {'id': str(uuid.uuid4()), 'name': 'Mentorship'},
            {'id': str(uuid.uuid4()), 'name': 'Connect with new parts of the organization'},
        ]
    )

    op.create_table(
        'user_product_preference',
        sa.Column('user_id', UUID, ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('product_id', UUID, ForeignKey('product_preference.id'), primary_key=True),
    )


def downgrade():
    op.drop_table('user_product_preference')
    op.drop_table('product_preference')
