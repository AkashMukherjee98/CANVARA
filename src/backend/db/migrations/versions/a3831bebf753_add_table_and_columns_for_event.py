"""add table and columns for event

Revision ID: a3831bebf753
Revises: fa3e1f345bb0
Create Date: 2021-12-02 13:11:52.957722

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'a3831bebf753'
down_revision = 'fa3e1f345bb0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'event',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('primary_organizer_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('secondary_organizer_id', UUID, sa.ForeignKey('canvara_user.id')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('start_datetime', sa.DateTime(timezone=True)),
        sa.Column('end_datetime', sa.DateTime(timezone=True)),
        sa.Column('location_id', UUID, sa.ForeignKey('location.id')),
        sa.Column('logo_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('video_overview_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('details', JSONB),
        sa.Column('status', sa.String(127), default="active"),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('event')
