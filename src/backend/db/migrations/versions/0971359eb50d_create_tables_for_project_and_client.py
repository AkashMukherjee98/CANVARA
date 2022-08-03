"""create tables for project and client

Revision ID: 0971359eb50d
Revises: 9d381fd7045c
Create Date: 2022-07-29 17:43:33.412125

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '0971359eb50d'
down_revision = '9d381fd7045c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(  # pylint: disable=no-member
        'client',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('logo_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'project',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id'), nullable=False),
        sa.Column('client_id', UUID, sa.ForeignKey('client.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )


def downgrade():
    op.drop_table('project')
    op.drop_table('client')
