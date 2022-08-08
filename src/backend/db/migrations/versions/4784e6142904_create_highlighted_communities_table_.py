"""Create highlighted communities table for gigs

Revision ID: 4784e6142904
Revises: 616a12786534
Create Date: 2022-02-04 01:05:01.786419

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '4784e6142904'
down_revision = '616a12786534'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'post_community',
        sa.Column('post_id', UUID, sa.ForeignKey('post.id'), primary_key=True),
        sa.Column('community_id', UUID, sa.ForeignKey('community.id'), primary_key=True)
    )


def downgrade():
    op.drop_table('post_community')
