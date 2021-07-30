"""remove user location_id

Revision ID: b2c2f6557346
Revises: 16423008a08a
Create Date: 2021-07-30 11:57:06.489193

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c2f6557346'
down_revision = '16423008a08a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('canvara_user') as batch_op:
        batch_op.drop_column('location_id')


def downgrade():
    with op.batch_alter_table('canvara_user') as batch_op:
        batch_op.add_column(sa.Column('location_id', UUID, sa.ForeignKey('location.id')))
