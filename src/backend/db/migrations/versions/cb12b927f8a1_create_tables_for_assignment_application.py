"""create tables for assignment application

Revision ID: cb12b927f8a1
Revises: 6507e3c84857
Create Date: 2022-08-03 23:23:19.932765

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'cb12b927f8a1'
down_revision = '6507e3c84857'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'assignment_application',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('assignment_id', UUID, sa.ForeignKey('assignment.id'), nullable=False),
        sa.Column('applicant_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('details', JSONB),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True)),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=False)
    )


def downgrade():
    op.drop_table('assignment_application')
