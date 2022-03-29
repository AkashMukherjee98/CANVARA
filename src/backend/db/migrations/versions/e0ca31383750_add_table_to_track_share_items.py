"""add table to track share items

Revision ID: e0ca31383750
Revises: 187a63e91710
Create Date: 2022-03-28 13:30:04.999587

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'e0ca31383750'
down_revision = '187a63e91710'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'share',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('shared_by_user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('shared_with_user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('item_id', UUID, nullable=False),
        sa.Column('item_type', sa.String(50), nullable=False),
        sa.Column('message', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )


def downgrade():
    op.drop_table('share')
