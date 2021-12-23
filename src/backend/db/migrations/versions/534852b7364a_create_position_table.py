"""create position table

Revision ID: 534852b7364a
Revises: e3d9da8a3b50
Create Date: 2021-12-22 19:22:53.131196

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, INT8RANGE


# revision identifiers, used by Alembic.
revision = '534852b7364a'
down_revision = 'e3d9da8a3b50'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'position',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('manager_id', UUID, ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('location_id', UUID, ForeignKey('location.id'), nullable=False),
        sa.Column('role_type', sa.String(255), nullable=False),
        sa.Column('role', sa.String(255), nullable=False),
        sa.Column('department', sa.String(255), nullable=False),
        sa.Column('pay_range', INT8RANGE),
        sa.Column('details', JSONB),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )


def downgrade():
    op.drop_table('position')
