"""create table for role based authorization

Revision ID: e49eb831622c
Revises: 10de31416faf
Create Date: 2022-06-29 21:18:06.658512

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = 'e49eb831622c'
down_revision = '10de31416faf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_role',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id')),
        sa.Column('role', sa.String(255), nullable=False),
        sa.Column('permissions', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime)
    )

    op.create_table(
        'user_role_mapping',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id')),
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id')),
        sa.Column('user_role_id', UUID, sa.ForeignKey('user_role.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime)
    )


def downgrade():
    op.drop_table('user_role_mapping')
    op.drop_table('user_role')
