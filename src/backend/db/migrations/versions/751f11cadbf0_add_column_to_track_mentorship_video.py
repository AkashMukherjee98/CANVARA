"""add column to track mentorship video

Revision ID: 751f11cadbf0
Revises: e8947dd828d8
Create Date: 2021-11-24 16:21:18.899174

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '751f11cadbf0'
down_revision = 'e8947dd828d8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('canvara_user', sa.Column('mentorship_video_id', UUID))


def downgrade():
    op.drop_column('canvara_user', 'mentorship_video_id')
