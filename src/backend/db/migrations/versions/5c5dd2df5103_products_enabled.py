"""products enabled

Revision ID: 5c5dd2df5103
Revises: bf39805e2e04
Create Date: 2022-08-21 13:15:45.603954

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '5c5dd2df5103'
down_revision = 'bf39805e2e04'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customer') as batch_op:
        batch_op.add_column(sa.Column('products_enabled', JSONB))


def downgrade():
    with op.batch_alter_table('customer') as batch_op:
        batch_op.drop_column('products_enabled')
