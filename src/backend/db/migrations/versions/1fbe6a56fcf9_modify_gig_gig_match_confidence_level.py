"""Modify gig gig match confidence level

Revision ID: 1fbe6a56fcf9
Revises: 1b3d3725fea9
Create Date: 2022-04-22 09:28:03.173602

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '1fbe6a56fcf9'
down_revision = '1b3d3725fea9'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE gig_gig_match ALTER COLUMN confidence_level TYPE real")


def downgrade():
    op.execute("ALTER TABLE gig_gig_match ALTER COLUMN confidence_level TYPE int")
