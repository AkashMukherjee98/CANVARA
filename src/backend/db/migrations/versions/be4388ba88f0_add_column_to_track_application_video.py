"""add column to track application video

Revision ID: be4388ba88f0
Revises: 0f8331ab2498
Create Date: 2021-07-21 15:54:58.367920

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be4388ba88f0'
down_revision = '0f8331ab2498'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('application', sa.Column('description_video_id', UUID, sa.ForeignKey('user_upload.id')))


def downgrade():
    op.drop_column('application', 'description_video_id')
