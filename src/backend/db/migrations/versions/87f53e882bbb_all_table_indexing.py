"""all_table_indexing

Revision ID: 87f53e882bbb
Revises: a98d2026c1fa
Create Date: 2022-05-17 20:07:41.021903

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '87f53e882bbb'
down_revision = 'a98d2026c1fa'
branch_labels = None
depends_on = None


def upgrade():
    # Table name: application
    op.create_index(op.f('application_post_id'), 'application', ['post_id'])
    # Table name: canvara_user
    op.create_index(op.f('canvara_user_manager_id'), 'canvara_user', ['manager_id'])
    op.create_index(op.f('canvara_user_profile_picture_id'), 'canvara_user', ['profile_picture_id'])
    # Table name: community
    op.create_index(op.f('community_status'), 'community', ['status'])
    op.create_index(op.f('community_primary_moderator_id'), 'community', ['primary_moderator_id'])
    op.create_index(op.f('community_secondary_moderator_id'), 'community', ['secondary_moderator_id'])
    # Table name: community_announcement
    op.create_index(op.f('community_announcement_community_id'), 'community_announcement', ['community_id'])
    op.create_index(op.f('community_announcement_status'), 'community_announcement', ['status'])
    # Table name: community_membership
    op.create_index(op.f('community_membership_member_id'), 'community_membership', ['member_id'])
    op.create_index(op.f('community_membership_community_id'), 'community_membership', ['community_id'])
    op.create_index(op.f('community_membership_status'), 'community_membership', ['status'])
    # Table name: event
    op.create_index(op.f('event_sponsor_community_id'), 'event', ['sponsor_community_id'])
    op.create_index(op.f('event_status'), 'event', ['status'])
    op.create_index(op.f('event_primary_organizer_id'), 'event', ['primary_organizer_id'])
    op.create_index(op.f('event_secondary_organizer_id'), 'event', ['secondary_organizer_id'])
    # Table name: event_comment
    op.create_index(op.f('event_comment_event_id'), 'event_comment', ['event_id'])
    op.create_index(op.f('event_comment_status'), 'event_comment', ['status'])
    # Table name: event_rsvp
    op.create_index(op.f('event_rsvp_guest_id'), 'event_rsvp', ['guest_id'])
    op.create_index(op.f('event_rsvp_event_id'), 'event_rsvp', ['event_id'])
    op.create_index(op.f('event_rsvp_status'), 'event_rsvp', ['status'])
    # Table name: offer
    op.create_index(op.f('offer_offerer_id'), 'offer', ['offerer_id'])
    op.create_index(op.f('offer_status'), 'offer', ['status'])
    # Table name: offer_proposal
    op.create_index(op.f('offer_proposal_offer_id'), 'offer_proposal', ['offer_id'])
    op.create_index(op.f('offer_proposal_proposer_id'), 'offer_proposal', ['proposer_id'])
    op.create_index(op.f('offer_proposal_status'), 'offer_proposal', ['status'])
    # Table name: position
    op.create_index(op.f('position_manager_id'), 'position', ['manager_id'])
    op.create_index(op.f('position_status'), 'position', ['status'])
    # Table name: post
    op.create_index(op.f('post_owner_id'), 'post', ['owner_id'])
    op.create_index(op.f('post_post_type_id'), 'post', ['post_type_id'])
    op.create_index(op.f('post_location_id'), 'post', ['location_id'])
    op.create_index(op.f('post_status'), 'post', ['status'])


def downgrade():
    # Table name: application
    op.drop_index('application_post_id', table_name='application')
    # Table name: canvara_user
    op.drop_index('canvara_user_manager_id', table_name='canvara_user')
    op.drop_index('canvara_user_profile_picture_id', table_name='canvara_user')
    # Table name: community
    op.drop_index('community_status', table_name='community')
    op.drop_index('community_primary_moderator_id', table_name='community')
    op.drop_index('community_secondary_moderator_id', table_name='community')
    # Table name: community_announcement
    op.drop_index('community_announcement_community_id', table_name='community_announcement')
    op.drop_index('community_announcement_status', table_name='community_announcement')
    # Table name: community_membership
    op.drop_index('community_membership_member_id', table_name='community_membership')
    op.drop_index('community_membership_community_id', table_name='community_membership')
    op.drop_index('community_membership_status', table_name='community_membership')
    # Table name: event
    op.drop_index('event_sponsor_community_id', table_name='event')
    op.drop_index('event_status', table_name='event')
    op.drop_index('event_primary_organizer_id', table_name='event')
    op.drop_index('event_secondary_organizer_id', table_name='event')
    # Table name: event_comment
    op.drop_index('event_comment_event_id', table_name='event_comment')
    op.drop_index('event_comment_status', table_name='event_comment')
    # Table name: event_rsvp
    op.drop_index('event_rsvp_guest_id', table_name='event_rsvp')
    op.drop_index('event_rsvp_event_id', table_name='event_rsvp')
    op.drop_index('event_rsvp_status', table_name='event_rsvp')
    # Table name: offer
    op.drop_index('offer_offerer_id', table_name='offer')
    op.drop_index('offer_status', table_name='offer')
    # Table name: offer_proposal
    op.drop_index('offer_proposal_offer_id', table_name='offer_proposal')
    op.drop_index('offer_proposal_proposer_id', table_name='offer_proposal')
    op.drop_index('offer_proposal_status', table_name='offer_proposal')
    # Table name: position
    op.drop_index('position_manager_id', table_name='position')
    op.drop_index('position_status', table_name='position')
    # Table name: post
    op.drop_index('post_owner_id', table_name='post')
    op.drop_index('post_post_type_id', table_name='post')
    op.drop_index('post_location_id', table_name='post')
    op.drop_index('post_status', table_name='post')
