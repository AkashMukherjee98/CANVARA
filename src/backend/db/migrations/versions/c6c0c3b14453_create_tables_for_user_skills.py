"""create tables for user skills

Revision ID: c6c0c3b14453
Revises: e63d316c4e6e
Create Date: 2021-06-15 02:08:31.072937

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.schema import ForeignKey
import sqlalchemy as sa


# revision identifiers, used by Alembic.
# pylint: disable=invalid-name
revision = 'c6c0c3b14453'
down_revision = 'e63d316c4e6e'
branch_labels = None
depends_on = None
# pylint: enable=invalid-name


def upgrade():
    op.create_table(  # pylint: disable=no-member
        'skill',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('is_custom', sa.Boolean)
    )

    op.create_table(  # pylint: disable=no-member
        'user_current_skill',
        sa.Column('user_id', UUID, ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('skill_id', UUID, ForeignKey('skill.id'), primary_key=True),
        sa.Column('level', sa.Integer, nullable=False),
    )

    op.create_table(  # pylint: disable=no-member
        'user_desired_skill',
        sa.Column('user_id', UUID, ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('skill_id', UUID, ForeignKey('skill.id'), primary_key=True),
    )


def downgrade():
    # pylint: disable=no-member
    op.drop_table('user_desired_skill')
    op.drop_table('user_current_skill')
    op.drop_table('skill')
    # pylint: enable=no-member
