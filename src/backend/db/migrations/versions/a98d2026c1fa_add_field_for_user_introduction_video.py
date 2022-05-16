"""Add field for user introduction video

Revision ID: a98d2026c1fa
Revises: 1fbe6a56fcf9
Create Date: 2022-04-29 15:48:00.589280

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'a98d2026c1fa'
down_revision = '1fbe6a56fcf9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('canvara_user', sa.Column('introduction_video_id', UUID, sa.ForeignKey('user_upload.id')))


def downgrade():
    op.drop_column('canvara_user', 'introduction_video_id')
