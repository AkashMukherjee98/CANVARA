"""add column to track background picture

Revision ID: 27855dec2c30
Revises: 8ee49b91feae
Create Date: 2022-01-04 15:05:35.991163

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27855dec2c30'
down_revision = '8ee49b91feae'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('canvara_user', sa.Column('background_picture_id', UUID, sa.ForeignKey('user_upload.id')))

    # Background picture upload for admin
    op.create_table(
        'backgroundpicture',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id')),
        sa.Column('upload_id', UUID, sa.ForeignKey('user_upload.id'), primary_key=True),
    )


def downgrade():
    op.drop_column('canvara_user', 'background_picture_id')

    op.drop_table('backgroundpicture')
