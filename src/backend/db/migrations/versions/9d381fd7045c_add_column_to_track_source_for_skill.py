"""add column to track source for skill

Revision ID: 9d381fd7045c
Revises: 6f9ff0cfbe4d
Create Date: 2022-07-22 20:08:25.825815

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d381fd7045c'
down_revision = '6f9ff0cfbe4d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('skill', sa.Column('source', sa.String(25)))


def downgrade():
    op.drop_column('skill', 'source')
