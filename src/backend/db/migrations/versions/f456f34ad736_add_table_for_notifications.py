"""add table for notifications

Revision ID: f456f34ad736
Revises: cfb4e27d6c77
Create Date: 2021-08-12 21:30:46.445252

"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f456f34ad736'
down_revision = 'cfb4e27d6c77'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notification',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('type', sa.String(255), nullable=False),
        sa.Column('data', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(31), nullable=False),
    )


def downgrade():
    op.drop_table('notification')
