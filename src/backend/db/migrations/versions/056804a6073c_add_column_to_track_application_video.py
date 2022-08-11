"""add column to track application video

Revision ID: 056804a6073c
Revises: cb12b927f8a1
Create Date: 2022-08-11 17:56:39.427690

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '056804a6073c'
down_revision = 'cb12b927f8a1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('assignment_application', sa.Column('application_video_id', UUID, sa.ForeignKey('user_upload.id')))


def downgrade():
    op.drop_column('assignment_application', 'application_video_id')
