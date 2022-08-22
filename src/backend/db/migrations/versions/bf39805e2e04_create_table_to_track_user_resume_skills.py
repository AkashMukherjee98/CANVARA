"""create table to track user resume skills

Revision ID: bf39805e2e04
Revises: 056804a6073c
Create Date: 2022-08-22 20:07:20.523953

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'bf39805e2e04'
down_revision = '056804a6073c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(  # pylint: disable=no-member
        'user_resume_skill',
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id'), primary_key=True),
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('skill_id', UUID, sa.ForeignKey('skill.id'), primary_key=True),
        sa.Column('confidence_level', sa.Integer)
    )


def downgrade():
    op.drop_table('user_resume_skill')
