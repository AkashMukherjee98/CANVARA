"""add tables to track post performers

Revision ID: 9f7e71ddb88f
Revises: f456f34ad736
Create Date: 2021-08-31 15:40:34.385508

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f7e71ddb88f'
down_revision = 'f456f34ad736'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'performer',
        sa.Column('application_id', UUID, sa.ForeignKey('application.id'), primary_key=True),
        sa.Column('status', sa.String(31), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('performer')
