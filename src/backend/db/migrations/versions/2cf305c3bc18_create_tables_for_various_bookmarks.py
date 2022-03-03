"""Create tables for various bookmarks

Revision ID: 2cf305c3bc18
Revises: b80522f1dd04
Create Date: 2022-02-28 17:33:55.099086

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '2cf305c3bc18'
down_revision = 'b80522f1dd04'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'people_bookmark',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('people_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    op.create_table(
        'community_bookmark',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('community_id', UUID, sa.ForeignKey('community.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    op.create_table(
        'event_bookmark',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('event_id', UUID, sa.ForeignKey('event.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    op.create_table(
        'offer_bookmark',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('offer_id', UUID, sa.ForeignKey('offer.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    op.create_table(
        'position_bookmark',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('position_id', UUID, sa.ForeignKey('position.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('people_bookmark')
    op.drop_table('community_bookmark')
    op.drop_table('event_bookmark')
    op.drop_table('offer_bookmark')
    op.drop_table('position_bookmark')
