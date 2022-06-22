"""Add column to track user resume file

Revision ID: c33c9f9c33db
Revises: 0818eb53b001
Create Date: 2022-05-27 14:49:02.983565

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'c33c9f9c33db'
down_revision = '0818eb53b001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('canvara_user', sa.Column('resume_file_id', UUID, sa.ForeignKey('user_upload.id')))


def downgrade():
    op.drop_column('canvara_user', 'resume_file_id')
