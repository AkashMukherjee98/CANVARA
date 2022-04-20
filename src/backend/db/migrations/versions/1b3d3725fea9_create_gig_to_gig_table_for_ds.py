"""Create gig to gig table for ds

Revision ID: 1b3d3725fea9
Revises: e0ca31383750
Create Date: 2022-04-20 10:42:52.738515

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '1b3d3725fea9'
down_revision = 'e0ca31383750'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'gig_gig_match',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('source_gig_id', UUID, sa.ForeignKey('post.id')),
        sa.Column('recommended_gig_id', UUID, sa.ForeignKey('post.id')),
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(255), nullable=False),
        sa.Column('confidence_level', sa.Integer, nullable=False),
        sa.Column('recommender_system', sa.String(255), nullable=True)
    )


def downgrade():
    op.drop_table('gig_gig_match')
