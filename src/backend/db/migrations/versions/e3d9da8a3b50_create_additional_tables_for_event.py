"""create additional tables for event

Revision ID: e3d9da8a3b50
Revises: a3831bebf753
Create Date: 2021-12-20 11:34:55.155771

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'e3d9da8a3b50'
down_revision = 'a3831bebf753'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'event_comment',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('event_id', UUID, sa.ForeignKey('event.id'), nullable=False),
        sa.Column('created_by', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('comment', sa.Text),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'event_rsvp',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('event_id', UUID, sa.ForeignKey('event.id'), nullable=False),
        sa.Column('guest_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'event_gallery',
        sa.Column('event_id', UUID, sa.ForeignKey('event.id'), primary_key=True),
        sa.Column('upload_id', UUID, sa.ForeignKey('user_upload.id'), primary_key=True),
    )


def downgrade():
    op.drop_table('event_comment')
    op.drop_table('event_rsvp')
    op.drop_table('event_gallery')
