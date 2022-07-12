"""add customer_id field to activities

Revision ID: f118030d19ab
Revises: ded19f082a02
Create Date: 2022-07-11 22:39:11.729910

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'f118030d19ab'
down_revision = 'ded19f082a02'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('activity', sa.Column('customer_id', UUID, sa.ForeignKey('customer.id')))


def downgrade():
    op.drop_column('activity', 'customer_id')
