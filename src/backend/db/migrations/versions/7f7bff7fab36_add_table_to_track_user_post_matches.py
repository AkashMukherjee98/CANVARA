"""add table to track user-post matches

Revision ID: 7f7bff7fab36
Revises: 79f58fe08541
Create Date: 2021-07-06 02:23:16.046958

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f7bff7fab36'
down_revision = '79f58fe08541'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_post_match',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id')),
        sa.Column('post_id', UUID, sa.ForeignKey('post.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(255), nullable=False),
        sa.Column('confidence_level', sa.Integer, nullable=False),
        sa.UniqueConstraint('user_id', 'post_id'),
    )


def downgrade():
    op.drop_table('user_post_match')
