"""combine desired and required skills for posts

Revision ID: cfb4e27d6c77
Revises: b2c2f6557346
Create Date: 2021-08-10 20:32:55.760624

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cfb4e27d6c77'
down_revision = 'b2c2f6557346'
branch_labels = None
depends_on = None


def upgrade():
    # Rename the table since it will now contain both required and desired skills
    op.rename_table('post_required_skill', 'post_skill')

    # Add a new column to track whether the skill is required and set all current skills to required
    op.add_column('post_skill', sa.Column('is_required', sa.Boolean))
    op.execute("UPDATE post_skill SET is_required = TRUE")
    op.alter_column('post_skill', 'is_required', nullable=False)

    # Copy over all the desired skills, with skill level set to 0 to keep the current matching behavior
    op.execute(
        "INSERT INTO post_skill(post_id, skill_id, level, is_required) "
        "SELECT post_id, skill_id, 0, FALSE FROM post_desired_skill")

    op.drop_table('post_desired_skill')


def downgrade():
    # Recreate the desired skills table and move all the desired skills back
    op.create_table(
        'post_desired_skill',
        sa.Column('post_id', UUID, sa.ForeignKey('post.id'), primary_key=True),
        sa.Column('skill_id', UUID, sa.ForeignKey('skill.id'), primary_key=True),
    )

    op.execute(
        "INSERT INTO post_desired_skill(post_id, skill_id) "
        "SELECT post_id, skill_id FROM post_skill WHERE NOT is_required")

    op.execute("DELETE FROM post_skill WHERE NOT is_required")

    op.drop_column('post_skill', 'is_required')
    op.rename_table('post_skill', 'post_required_skill')
