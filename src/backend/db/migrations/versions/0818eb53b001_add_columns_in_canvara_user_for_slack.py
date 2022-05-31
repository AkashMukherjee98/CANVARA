"""add_columns_in_canvara_user_for_slack

Revision ID: 0818eb53b001
Revises: 87f53e882bbb
Create Date: 2022-05-23 20:51:31.059402

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0818eb53b001'
down_revision = '87f53e882bbb'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('canvara_user') as batch_op:
        batch_op.add_column(sa.Column('slack_id', sa.String(255)))
        batch_op.add_column(sa.Column('workspace_id', sa.String(255)))


def downgrade():
    with op.batch_alter_table('canvara_user') as batch_op:
        batch_op.drop_column('slack_id')
        batch_op.drop_column('workspace_id')
