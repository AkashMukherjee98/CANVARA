"""add table to track feedback

Revision ID: e8947dd828d8
Revises: 9f7e71ddb88f
Create Date: 2021-08-31 22:28:05.663465

"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8947dd828d8'
down_revision = '9f7e71ddb88f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'feedback',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('author_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('post_id', UUID, sa.ForeignKey('post.id'), nullable=False),
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('user_role', sa.String(31), nullable=False),
        sa.Column('feedback', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('author_id', 'post_id', 'user_id'),
    )


def downgrade():
    op.drop_table('feedback')
