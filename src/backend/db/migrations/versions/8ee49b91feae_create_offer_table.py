"""create offer table

Revision ID: 8ee49b91feae
Revises: 63e2bfb02565
Create Date: 2022-01-07 12:25:22.995912

"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ee49b91feae'
down_revision = '63e2bfb02565'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'offer',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('offerer_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('overview_video_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('details', JSONB),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )


def downgrade():
    op.drop_table('offer')
