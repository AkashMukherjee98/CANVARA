"""Set default value for skill expert badge

Revision ID: ad843a173d77
Revises: e66fa0414071
Create Date: 2022-02-09 14:19:04.776652

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ad843a173d77'
down_revision = 'e66fa0414071'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE user_current_skill SET is_expert = false WHERE is_expert IS NULL"
    )
    op.execute(
        "ALTER TABLE user_current_skill ALTER COLUMN is_expert SET NOT NULL"
    )
    op.execute(
        "ALTER TABLE ONLY user_current_skill ALTER COLUMN is_expert SET DEFAULT false"
    )


def downgrade():
    op.execute(
        "ALTER TABLE user_current_skill ALTER COLUMN is_expert DROP NOT NULL;"
    )
    op.execute(
        "ALTER TABLE user_current_skill ALTER COLUMN is_expert DROP DEFAULT"
    )
