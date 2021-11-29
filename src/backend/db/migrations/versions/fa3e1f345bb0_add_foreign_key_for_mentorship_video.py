"""Add foreign key for mentorship video

Revision ID: fa3e1f345bb0
Revises: 751f11cadbf0
Create Date: 2021-11-29 13:56:20.529959

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'fa3e1f345bb0'
down_revision = '751f11cadbf0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        u'canvara_user_mentorship_video_id_fkey', 'canvara_user', 'user_upload', ['mentorship_video_id'], ['id'])


def downgrade():
    op.drop_constraint(u'canvara_user_mentorship_video_id_fkey', 'canvara_user', type_='foreignkey')
