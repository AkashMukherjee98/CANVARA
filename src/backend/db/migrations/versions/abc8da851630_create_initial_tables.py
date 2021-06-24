"""create initial tables

Revision ID: abc8da851630
Revises:
Create Date: 2021-06-10 11:58:58.753430

"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql.schema import ForeignKey
import sqlalchemy as sa


# revision identifiers, used by Alembic.
# pylint: disable=invalid-name
revision = 'abc8da851630'
down_revision = None
branch_labels = None
depends_on = None
# pylint: enable=invalid-name


def upgrade():
    op.create_table(  # pylint: disable=no-member
        'customer',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
    )

    # Note: 'user' is a reserved keyword in postgres so we use 'canvara_user' instead
    op.create_table(  # pylint: disable=no-member
        'canvara_user',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('customer_id', UUID, ForeignKey('customer.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('profile', JSONB)
    )

    op.create_table(  # pylint: disable=no-member
        'post',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('owner_id', UUID, ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False),
        sa.Column('details', JSONB)
    )

    # Note: status is a string for now, but may be converted to an Enum later
    op.create_table(  # pylint: disable=no-member
        'application',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('user_id', UUID, ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('post_id', UUID, ForeignKey('post.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(31), nullable=False),
        sa.Column('details', JSONB)
    )

def downgrade():
    # pylint: disable=no-member
    op.drop_table('application')
    op.drop_table('post')
    op.drop_table('canvara_user')
    op.drop_table('customer')
    # pylint: enable=no-member
