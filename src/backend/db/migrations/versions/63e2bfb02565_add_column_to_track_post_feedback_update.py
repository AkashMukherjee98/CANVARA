"""add column to track post feedback update

Revision ID: 63e2bfb02565
Revises: 27855dec2c30
Create Date: 2022-01-05 15:35:28.552195

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63e2bfb02565'
down_revision = '27855dec2c30'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('feedback', sa.Column('last_updated_at', sa.DateTime))


def downgrade():
    op.drop_column('feedback', 'last_updated_at')
