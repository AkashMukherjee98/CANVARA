"""add skill expert flag for users

Revision ID: e66fa0414071
Revises: 4784e6142904
Create Date: 2022-02-08 15:04:11.199056

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e66fa0414071'
down_revision = '4784e6142904'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_current_skill', sa.Column('is_expert', sa.Boolean()))


def downgrade():
    op.drop_column('user_current_skill', 'is_expert')
