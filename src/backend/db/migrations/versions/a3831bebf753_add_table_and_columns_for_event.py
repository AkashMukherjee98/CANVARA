"""add table and columns for event

Revision ID: a3831bebf753
Revises: fa3e1f345bb0
Create Date: 2021-12-02 13:11:52.957722

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


# revision identifiers, used by Alembic.
revision = 'a3831bebf753'
down_revision = 'fa3e1f345bb0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'event',
        sa.Column('id', UUID, primary_key=True),
        # NOTE: (Santanu) To reduce number of tables I created UUID[] field for organizers(user),
        # However PostgreSQL currently not supported for FK relationship for ARRAY type fields!
        sa.Column('organizers', ARRAY(UUID)),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('event_date', sa.Date),
        sa.Column('start_time', sa.Time),
        sa.Column('end_time', sa.Time),
        sa.column('people_needed', sa.Integer),
        sa.Column('location', sa.Text),
        sa.Column('language', sa.String(255)),
        sa.Column('logo_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('overview', sa.Text),
        sa.Column('overview_video_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('details', JSONB),
        sa.Column('status', sa.String(127), default="active"),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('event')
