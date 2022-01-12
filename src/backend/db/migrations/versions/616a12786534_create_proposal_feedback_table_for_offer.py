"""create proposal feedback table for offer

Revision ID: 616a12786534
Revises: 8ee49b91feae
Create Date: 2022-01-07 16:50:09.529178

"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '616a12786534'
down_revision = '8ee49b91feae'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'offer_proposal',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('proposer_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('offer_id', UUID, sa.ForeignKey('offer.id'), nullable=False),
        sa.Column('overview_video_id', UUID, sa.ForeignKey('user_upload.id')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(127), nullable=False),
        sa.Column('details', JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'offer_proposal_progress',
        sa.Column('proposal_id', UUID, sa.ForeignKey('offer_proposal.id'), primary_key=True),
        sa.Column('status', sa.String(31), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True)),
        sa.Column('end_date', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'offer_feedback',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('author_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('offer_id', UUID, sa.ForeignKey('offer.id'), nullable=False),
        sa.Column('user_id', UUID, sa.ForeignKey('canvara_user.id'), nullable=False),
        sa.Column('user_role', sa.String(31), nullable=False),
        sa.Column('feedback', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('author_id', 'offer_id', 'user_id'),
    )


def downgrade():
    op.drop_table('offer_feedback')
    op.drop_table('offer_proposal_progress')
    op.drop_table('offer_proposal')
