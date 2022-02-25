"""Modify user-post-match for DS operations

Revision ID: b80522f1dd04
Revises: ad843a173d77
Create Date: 2022-02-24 17:08:15.810039

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'b80522f1dd04'
down_revision = 'ad843a173d77'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_post_match', sa.Column('customer_id', UUID, sa.ForeignKey('customer.id')))
    op.execute("UPDATE user_post_match SET customer_id = canvara_user.customer_id \
        FROM canvara_user WHERE canvara_user.id = user_post_match.user_id")

    op.execute("ALTER TABLE user_post_match ALTER COLUMN confidence_level TYPE real")

    op.execute("ALTER TABLE user_post_match DROP CONSTRAINT IF EXISTS user_post_match_user_id_post_id_key")


def downgrade():
    op.drop_column('user_post_match', 'customer_id')

    op.execute("ALTER TABLE user_post_match ALTER COLUMN confidence_level TYPE int")
