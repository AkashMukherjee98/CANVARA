"""create community associated tables

Revision ID: 3c95cc5dd790
Revises: 580defda3a46
Create Date: 2021-12-13 14:45:20.181814

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '3c95cc5dd790'
down_revision = '580defda3a46'
branch_labels = None
depends_on = None


def upgrade():
    # Remove deprecated `announcements` key from community table
    op.execute(
        "UPDATE community SET details = details - 'announcements'"
    )

    op.create_table(
        'community_announcement',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('community_id', UUID, sa.ForeignKey('community.id'), nullable=False),
        sa.Column('created_by', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('announcement', sa.Text),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'community_membership',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('community_id', UUID, sa.ForeignKey('community.id'), nullable=False),
        sa.Column('member_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'community_gallery',
        sa.Column('community_id', UUID, sa.ForeignKey('community.id'), primary_key=True),
        sa.Column('upload_id', UUID, sa.ForeignKey('user_upload.id'), primary_key=True),
    )


def downgrade():
    op.drop_table('community_announcement')
    op.drop_table('community_membership')
    op.drop_table('community_gallery')
