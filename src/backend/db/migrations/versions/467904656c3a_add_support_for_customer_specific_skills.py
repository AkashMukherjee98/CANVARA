"""add support for customer-specific skills

Revision ID: 467904656c3a
Revises: c6c0c3b14453
Create Date: 2021-06-25 13:58:14.063191

"""
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
# pylint: disable=invalid-name
revision = '467904656c3a'
down_revision = 'c6c0c3b14453'
branch_labels = None
depends_on = None
# pylint: enable=invalid-name


def upgrade():
    with op.batch_alter_table('skill') as batch_op:
        # customer_id is NULL for global skills available to all users
        # customer_id is NON NULL for customer-specific skills available only the users of that customer
        batch_op.add_column(sa.Column('customer_id', UUID, sa.ForeignKey('customer.id')))

        # normalized (lowercased) form of the skill name, used only for database constraints
        batch_op.add_column(sa.Column('internal_name', sa.String(255), nullable=False))

        # rename 'name' to 'display_name' for clarity
        # skill name as it should be displayed to the user
        batch_op.alter_column('name', new_column_name='display_name')
        batch_op.drop_constraint('skill_name_key')

        # keep track of when this skill was first added
        batch_op.add_column(sa.Column('created_at', sa.DateTime, nullable=False))

        # keep track of how many times this skill has been used
        batch_op.add_column(sa.Column('usage_count', sa.Integer, nullable=False, default=0))

        # add a unique index for all the global skills
        batch_op.create_index(
            'skill_internal_name_idx',
            ['internal_name'],
            unique=True,
            postgresql_where=(sa.text('skill.customer_id IS NULL')))

        # add another unique index for all the customer-specific skills
        batch_op.create_index(
            'skill_internal_name_customer_id_idx',
            ['internal_name', 'customer_id'],
            unique=True,
            postgresql_where=(sa.text('skill.customer_id IS NOT NULL')))

        # is_custom is replaced by customer_id
        batch_op.drop_column('is_custom')


def downgrade():
    with op.batch_alter_table('skill') as batch_op:
        batch_op.add_column(sa.Column('is_custom', sa.Boolean))

        batch_op.drop_column('usage_count')
        batch_op.drop_column('created_at')
        batch_op.alter_column('display_name', new_column_name='name')
        batch_op.create_unique_constraint('skill_name_key', ['name'])
        batch_op.drop_column('internal_name')
        batch_op.drop_column('customer_id')
