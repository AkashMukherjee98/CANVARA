"""add tables and columns for user profile

Revision ID: 16423008a08a
Revises: be4388ba88f0
Create Date: 2021-07-26 16:12:02.708168

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16423008a08a'
down_revision = 'be4388ba88f0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('canvara_user') as batch_op:
        batch_op.add_column(sa.Column('username', sa.String(255)))
        batch_op.add_column(sa.Column('manager_id', UUID, sa.ForeignKey('canvara_user.id')))
        batch_op.add_column(sa.Column('location_id', UUID, sa.ForeignKey('location.id')))

    op.create_table(
        'user_fun_fact',
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), primary_key=True),
        sa.Column('upload_id', UUID, sa.ForeignKey('user_upload.id'), primary_key=True),
    )


def downgrade():
    op.drop_table('user_fun_fact')
    with op.batch_alter_table('canvara_user') as batch_op:
        batch_op.drop_column('location_id')
        batch_op.drop_column('manager_id')
        batch_op.drop_column('username')
