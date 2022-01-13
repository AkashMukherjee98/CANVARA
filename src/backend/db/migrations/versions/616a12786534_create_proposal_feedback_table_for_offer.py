"""create proposal feedback table for offer

Revision ID: 616a12786534
Revises: 27855dec2c30
Create Date: 2022-01-07 16:50:09.529178

"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '616a12786534'
down_revision = '27855dec2c30'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'offer_proposal',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('offer_id', UUID, sa.ForeignKey('offer.id'), nullable=False),
        sa.Column('proposer_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('overview_video_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('details', JSONB),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('selected_at', sa.DateTime(timezone=True)),
        sa.Column('in_progress_at', sa.DateTime(timezone=True)),
        sa.Column('proposer_feedback', JSONB),
        sa.Column('offerer_feedback', JSONB),
        sa.Column('proposer_feedback_at', sa.DateTime(timezone=True)),
        sa.Column('offerer_feedback_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=False)
    )


def downgrade():
    op.drop_table('offer_proposal')
