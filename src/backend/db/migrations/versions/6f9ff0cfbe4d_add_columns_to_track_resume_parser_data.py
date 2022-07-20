"""add columns to track resume parser data

Revision ID: 6f9ff0cfbe4d
Revises: f118030d19ab
Create Date: 2022-07-18 20:33:51.586714

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '6f9ff0cfbe4d'
down_revision = 'f118030d19ab'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('canvara_user', sa.Column('resume_data', JSONB))


def downgrade():
    op.drop_column('canvara_user', 'resume_data')
