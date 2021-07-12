"""add tables to track post bookmarks and likes

Revision ID: 38a98007af17
Revises: 02b5fefb7497
Create Date: 2021-07-11 22:38:46.333793

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38a98007af17'
down_revision = '02b5fefb7497'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_post_bookmark',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('post_id', UUID, sa.ForeignKey('post.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    op.create_table(
        'user_post_like',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('post_id', UUID, sa.ForeignKey('post.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('user_post_like')
    op.drop_table('user_post_bookmark')
