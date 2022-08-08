"""add column to track profile picture

Revision ID: 0f8331ab2498
Revises: 38a98007af17
Create Date: 2021-07-13 14:24:53.901591

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f8331ab2498'
down_revision = '38a98007af17'
branch_labels = None
depends_on = None


def upgrade():
    # Move content_type to a dedicated column
    op.add_column('user_upload', sa.Column('content_type', sa.String(255)))
    op.execute(
        "UPDATE user_upload SET content_type = metadata->>'content_type'"
    )

    # And remove it from metadata
    op.execute(
        "UPDATE user_upload SET metadata = metadata - 'content_type'"
    )
    op.alter_column('user_upload', 'content_type', nullable=False)

    op.add_column('canvara_user', sa.Column('profile_picture_id', UUID, sa.ForeignKey('user_upload.id')))


def downgrade():
    op.drop_column('canvara_user', 'profile_picture_id')
    op.execute(
        "UPDATE user_upload SET metadata = jsonb_set(metadata, '{content_type}', to_jsonb(content_type))"
    )
    op.drop_column('user_upload', 'content_type')
