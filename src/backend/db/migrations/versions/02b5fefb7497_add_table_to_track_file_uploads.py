"""add table to track file uploads

Revision ID: 02b5fefb7497
Revises: 7f7bff7fab36
Create Date: 2021-07-09 00:56:12.646038

"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02b5fefb7497'
down_revision = '7f7bff7fab36'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_upload',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id')),
        sa.Column('bucket', sa.String(255), nullable=False),
        sa.Column('path', sa.String(1024), nullable=False),

        # 'status' can be 'created' or 'uploaded'
        sa.Column('status', sa.String(31), nullable=False),

        # additional 'metadata', including user id, original filename, content type etc.
        sa.Column('metadata', JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('bucket', 'path'),
    )

    with op.batch_alter_table('post') as batch_op:
        batch_op.add_column(sa.Column('description_video_id', UUID, sa.ForeignKey('user_upload.id')))
        batch_op.drop_column('video_url')


def downgrade():
    with op.batch_alter_table('post') as batch_op:
        batch_op.add_column(sa.Column('video_url', sa.String(2047)))
        batch_op.drop_column('description_video_id')
    op.drop_table('user_upload')
