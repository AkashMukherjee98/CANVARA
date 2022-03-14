"""create table for user recommendation system

Revision ID: 187a63e91710
Revises: 2cf305c3bc18
Create Date: 2022-03-14 16:59:33.007822

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '187a63e91710'
down_revision = '2cf305c3bc18'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_user_match',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('seeker_user_id', UUID, sa.ForeignKey('canvara_user.id')),
        sa.Column('recommendation_user_id', UUID, sa.ForeignKey('canvara_user.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(255), nullable=False),
        sa.Column('confidence_level', sa.Float, nullable=False),
        sa.Column('recommender_system', sa.String(255), nullable=False)
    )


def downgrade():
    op.drop_table('user_user_match')
