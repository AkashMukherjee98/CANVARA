"""create table for global activities

Revision ID: ded19f082a02
Revises: 10de31416faf
Create Date: 2022-07-11 18:30:51.694726

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = 'ded19f082a02'
down_revision = '10de31416faf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'activity_global',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id'), nullable=False),
        sa.Column('type', sa.String(255), nullable=False),
        sa.Column('data', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(31), nullable=False),
    )


def downgrade():
    op.drop_table('activity_global')
