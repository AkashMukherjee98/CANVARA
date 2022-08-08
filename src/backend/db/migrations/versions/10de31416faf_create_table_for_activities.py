"""create table for activities

Revision ID: 10de31416faf
Revises: c33c9f9c33db
Create Date: 2022-06-21 16:09:39.097492

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = '10de31416faf'
down_revision = 'c33c9f9c33db'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'activity',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('type', sa.String(255), nullable=False),
        sa.Column('data', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(31), nullable=False),
    )


def downgrade():
    op.drop_table('activity')
