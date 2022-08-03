"""create tables for assignment and relations

Revision ID: 6507e3c84857
Revises: 0971359eb50d
Create Date: 2022-08-03 16:03:36.186677

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '6507e3c84857'
down_revision = '0971359eb50d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'assignment',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id'), nullable=False),
        sa.Column('creator_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('project_id', UUID, sa.ForeignKey('project.id'), nullable=False),
        sa.Column('location_id', UUID, sa.ForeignKey('location.id')),
        sa.Column('video_description_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50)),
        sa.Column('start_date', sa.Date()),
        sa.Column('people_needed', sa.Integer),
        sa.Column('details', JSONB),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'assignment_skill',
        sa.Column('assignment_id', UUID, sa.ForeignKey('assignment.id'), primary_key=True),
        sa.Column('skill_id', UUID, sa.ForeignKey('skill.id'), primary_key=True),
        sa.Column('level', sa.Integer, nullable=False)
    )

    op.create_table(
        'assignment_bookmark',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('assignment_id', UUID, sa.ForeignKey('assignment.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('assignment_bookmark')
    op.drop_table('assignment_skill')
    op.drop_table('assignment')
