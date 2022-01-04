"""add column to track background picture

Revision ID: 27855dec2c30
Revises: 534852b7364a
Create Date: 2022-01-04 15:05:35.991163

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27855dec2c30'
down_revision = '534852b7364a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('canvara_user', sa.Column('background_picture_id', UUID, sa.ForeignKey('user_upload.id')))


def downgrade():
    op.drop_column('canvara_user', 'background_picture_id')
