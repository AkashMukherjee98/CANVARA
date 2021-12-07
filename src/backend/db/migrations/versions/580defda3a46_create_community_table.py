"""create community table

Revision ID: 580defda3a46
Revises: fa3e1f345bb0
Create Date: 2021-12-05 13:40:47.868040

"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '580defda3a46'
down_revision = 'fa3e1f345bb0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'community',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('owner_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('moderator_id', UUID, sa.ForeignKey('canvara_user.id')),
        sa.Column('logo_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('location_id', UUID, sa.ForeignKey('location.id')),
        sa.Column('language', sa.String(255)),
        sa.Column('video_overview_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('details', JSONB),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )


def downgrade():
    op.drop_table('community')
