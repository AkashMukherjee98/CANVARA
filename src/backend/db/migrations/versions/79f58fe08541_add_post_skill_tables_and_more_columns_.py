"""add post skill tables and more columns for post

Revision ID: 79f58fe08541
Revises: 4a9ce60d5e39
Create Date: 2021-07-01 23:49:35.482753

"""
import uuid

from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79f58fe08541'
down_revision = '4a9ce60d5e39'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'post_required_skill',
        sa.Column('post_id', UUID, sa.ForeignKey('post.id'), primary_key=True),
        sa.Column('skill_id', UUID, sa.ForeignKey('skill.id'), primary_key=True),
        sa.Column('level', sa.Integer, nullable=False),
    )

    op.create_table(
        'post_desired_skill',
        sa.Column('post_id', UUID, sa.ForeignKey('post.id'), primary_key=True),
        sa.Column('skill_id', UUID, sa.ForeignKey('skill.id'), primary_key=True),
    )

    # Add status column and set all posts to active for now
    op.add_column('post', sa.Column('status', sa.String(127)))
    op.execute(
        "UPDATE post SET status = 'active'"
    )
    op.alter_column('post', 'status', nullable=False)

    # Add more optional columns for posts
    with op.batch_alter_table('post') as batch_op:
        batch_op.add_column(sa.Column('candidate_description', sa.Text))
        batch_op.add_column(sa.Column('video_url', sa.String(2047)))
        batch_op.add_column(sa.Column('expiration_date', sa.Date))

    # Reorder and add more post types
    post_type_table = sa.table(
        'post_type',
        sa.column('id', UUID),
        sa.column('name', sa.String(255)),
        sa.column('rank', sa.Integer)
    )
    op.execute("UPDATE post_type SET rank = 7 WHERE name = 'Volunteering'")
    op.execute("UPDATE post_type SET rank = 2 WHERE name = 'Committee'")
    op.execute("UPDATE post_type SET rank = 3 WHERE name = 'Mentorship'")
    op.bulk_insert(post_type_table, [
        {'id': str(uuid.uuid4()), 'name': 'Innovation', 'rank': 4},
        {'id': str(uuid.uuid4()), 'name': 'Courses', 'rank': 5},
        {'id': str(uuid.uuid4()), 'name': 'Community', 'rank': 6},
    ])


def downgrade():
    op.execute("DELETE FROM post_type WHERE name IN ('Innovation', 'Courses', 'Community')")
    op.execute("UPDATE post_type SET rank = 4 WHERE name = 'Mentorship'")
    op.execute("UPDATE post_type SET rank = 3 WHERE name = 'Committee'")
    op.execute("UPDATE post_type SET rank = 2 WHERE name = 'Volunteering'")

    with op.batch_alter_table('post') as batch_op:
        batch_op.drop_column('expiration_date')
        batch_op.drop_column('video_url')
        batch_op.drop_column('candidate_description')
        batch_op.drop_column('status')
    op.drop_table('post_desired_skill')
    op.drop_table('post_required_skill')
