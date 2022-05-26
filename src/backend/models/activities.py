from .post import Post
from .application import Application
from .offer import Offer
from .offer import OfferProposal
from .position import Position

from .application import ApplicationStatus
from .offer import OfferProposalStatus

from .community import Community, CommunityMembership
from .event import Event, EventRSVP


class MyActivity():
    # Get activities counts
    @classmethod
    def activities_count(cls, tx, user):
        results = tx.execute('''SELECT
            (
                SELECT COUNT(id)
                    FROM post
                        WHERE
                            post.owner_id = :user_id
                            AND post.status != :deleted_status
            ) AS own_gigs,
            (
                SELECT COUNT(id)
                    FROM offer
                        WHERE
                            offer.offerer_id = :user_id
                            AND offer.status != :deleted_status
            ) AS own_offers,
            (
                SELECT COUNT(id)
                    FROM position
                        WHERE
                            position.manager_id = :user_id
                            AND position.status != :deleted_status
            ) AS own_positions,
            (
                SELECT COUNT(id)
                    FROM application
                        WHERE
                            application.user_id = :user_id
                            AND application.status IN :my_applications_status
            ) AS my_applications,
            (
                SELECT COUNT(id)
                    FROM offer_proposal
                        WHERE
                            offer_proposal.proposer_id = :user_id
                            AND offer_proposal.status IN :my_proposals_status
            ) AS my_proposals,
            (
                SELECT COUNT(id)
                    FROM application
                        WHERE
                            application.user_id = :user_id
                            AND application.status = :application_tasks_status
            ) AS application_tasks,
            (
                SELECT COUNT(id)
                    FROM offer_proposal
                        WHERE
                            offer_proposal.proposer_id = :user_id
                            AND offer_proposal.status IN :proposal_tasks_status
            ) AS proposal_tasks,
            (
                SELECT COUNT(community.id)
                    FROM community
                        JOIN
                            community_membership ON community_membership.community_id = community.id
                        WHERE
                            community.status = :active_status
                            AND community_membership.member_id = :user_id
            ) AS my_communities,
            (
                SELECT COUNT(event.id)
                    FROM event
                        JOIN
                            event_rsvp ON event_rsvp.event_id = event.id
                        WHERE
                            event.status = :active_status
                            AND event_rsvp.guest_id = :user_id
            ) AS my_events,
            (
                SELECT 0
            ) AS my_connections''', {
                'user_id': user.id,
                'deleted_status': 'deleted',
                'my_applications_status': (
                    ApplicationStatus.NEW.value,
                    ApplicationStatus.ACTIVE_READ.value
                ),
                'my_proposals_status': (
                    OfferProposalStatus.NEW.value,
                    OfferProposalStatus.ACTIVE_READ.value
                ),
                'application_tasks_status': ApplicationStatus.SELECTED.value,
                'proposal_tasks_status': (
                    OfferProposalStatus.SELECTED.value,
                    OfferProposalStatus.IN_PROGRESS.value,
                    OfferProposalStatus.COMPLETED.value
                ),
                'active_status': 'active'
            }
        )

        counts = results.fetchone()
        return dict(counts)

    # Get complete activities
    @classmethod
    def activities_one(cls, tx, user):
        own_gigs = tx.execute('''SELECT id, name
            FROM post
                WHERE
                    post.owner_id = :user_id
                    AND post.status != :deleted_status''', {
                        'user_id': user.id,
                        'deleted_status': 'deleted'
                    }
        )

        own_offers = tx.execute('''SELECT id, name
            FROM offer
                WHERE
                    offer.offerer_id = :user_id
                    AND offer.status != :deleted_status''', {
                        'user_id': user.id,
                        'deleted_status': 'deleted'
                    }
        )

        own_positions = tx.execute('''SELECT id, role
            FROM position
                WHERE
                    position.manager_id = :user_id
                    AND position.status != :deleted_status''', {
                        'user_id': user.id,
                        'deleted_status': 'deleted'
                    }
        )

        my_applications = tx.execute('''SELECT id, details->>'description' AS description
            FROM application
                WHERE
                    application.user_id = :user_id
                    AND application.status IN :my_applications_status''', {
                        'user_id': user.id,
                        'my_applications_status': (
                            ApplicationStatus.NEW.value,
                            ApplicationStatus.ACTIVE_READ.value
                        )
                    }
        )

        my_proposals = tx.execute('''SELECT id, name
            FROM offer_proposal
                WHERE
                    offer_proposal.proposer_id = :user_id
                    AND offer_proposal.status IN :my_proposals_status''', {
                        'user_id': user.id,
                        'my_proposals_status': (
                            OfferProposalStatus.NEW.value,
                            OfferProposalStatus.ACTIVE_READ.value
                        )
                    }
        )

        application_tasks = tx.execute('''SELECT id, details->>'description' AS description
            FROM application
                WHERE
                    application.user_id = :user_id
                    AND application.status = :application_tasks_status''', {
                        'user_id': user.id,
                        'application_tasks_status': ApplicationStatus.SELECTED.value
                    }
        )

        proposal_tasks = tx.execute('''SELECT id, name
            FROM offer_proposal
                WHERE
                    offer_proposal.proposer_id = :user_id
                    AND offer_proposal.status IN :proposal_tasks_status''', {
                        'user_id': user.id,
                        'proposal_tasks_status': (
                            OfferProposalStatus.SELECTED.value,
                            OfferProposalStatus.IN_PROGRESS.value,
                            OfferProposalStatus.COMPLETED.value
                        )
                    }
        )

        my_communities = tx.execute('''SELECT community.id, community.name
            FROM community
                JOIN
                    community_membership ON community_membership.community_id = community.id
                WHERE
                    community.status = :active_status
                    AND community_membership.member_id = :user_id''', {
                        'active_status': 'active',
                        'user_id': user.id
                    }
        )

        my_events = tx.execute('''SELECT event.id, event.name
            FROM event
                JOIN
                    event_rsvp ON event_rsvp.event_id = event.id
                WHERE
                    event.status = :active_status
                    AND event_rsvp.guest_id = :user_id''', {
                        'active_status': 'active',
                        'user_id': user.id
                    }
        )

        activities = {
            'own_gigs': [dict(row) for row in own_gigs],
            'own_offers': [dict(row) for row in own_offers],
            'own_positions': [dict(row) for row in own_positions],
            'my_applications': [dict(row) for row in my_applications],
            'my_proposals': [dict(row) for row in my_proposals],
            'application_tasks': [dict(row) for row in application_tasks],
            'proposal_tasks': [dict(row) for row in proposal_tasks],
            'my_communities': [dict(row) for row in my_communities],
            'my_events': [dict(row) for row in my_events],
            'my_connections': []
        }
        return activities

    # Get individual activities
    @classmethod
    def own_gigs(cls, tx, user):
        gigs = tx.query(Post).where(
            Post.owner_id == user.id,
            Post.status != 'deleted'
        )
        return list(gigs)

    @classmethod
    def own_offers(cls, tx, user):
        offers = tx.query(Offer).where(
            Offer.offerer_id == user.id,
            Offer.status != 'deleted'
        )
        return list(offers)

    @classmethod
    def own_positions(cls, tx, user):
        positions = tx.query(Position).where(
            Position.manager_id == user.id,
            Position.status != 'deleted'
        )
        return list(positions)

    @classmethod
    def my_applications(cls, tx, user, status):
        applications = tx.query(Application).join(Post).where(
            Post.id == Application.post_id,
            Application.user_id == user.id,
            Application.status.in_(status)
        )
        return list(applications)

    @classmethod
    def my_proposals(cls, tx, user, status):
        proposals = tx.query(OfferProposal).join(Offer).where(
            Offer.id == OfferProposal.offer_id,
            OfferProposal.proposer_id == user.id,
            OfferProposal.status.in_(status)
        )
        return list(proposals)

    @classmethod
    def my_communities(cls, tx, user):
        communities = tx.query(Community).join(CommunityMembership).where(
            Community.status == 'active',
            CommunityMembership.member_id == user.id
        )
        return list(communities)

    @classmethod
    def my_events(cls, tx, user):
        events = tx.query(Event).join(EventRSVP).where(
            Event.status == 'active',
            EventRSVP.guest_id == user.id
        )
        return list(events)

    @classmethod
    def my_connections(cls, tx, user):  # pylint: disable=unused-argument
        return list()
