import enum
import uuid
from datetime import datetime

from sqlalchemy import and_, func
from sqlalchemy.orm import relationship
from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase

from .post import Post
from .application import Application
from .application import ApplicationStatus
from .offer import Offer
from .offer import OfferProposal
from .offer import OfferProposalStatus
from .position import Position

from .community import Community, CommunityMembership
from .event import Event, EventRSVP


class ActivityType(enum.Enum):
    GIG_POSTED = 'gig_posted'
    APPLICATION_SUBMITTED = 'application_submitted'
    GIG_ASSIGNED = 'gig_assigned'
    APPLICATION_REJECTED = 'application_rejected'

    NEW_OFFER_POSTED = 'new_offer_posted'
    NEW_PROPOSAL = 'new_proposal'

    NEW_POSITION_POSTED = 'new_position_posted'

    NEW_COMMUNITY_CREATED = 'new_community_created'
    NEW_MEMBER_IN_YOUR_COMMUNITY = 'new_member_in_your_community'

    NEW_EVENT_POSTED = 'new_event_posted'

    NEW_EMPLOYEE_JOINED = 'new_employee_joined'
    NEW_ROLE = 'new_role'
    NEW_MENTORSHIP_BEING_OFFERED = 'new_mentorship_being_offered'

    @classmethod
    def lookup(cls, activity_type):
        try:
            return cls(activity_type)
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid activity type: {activity_type}") from ex

    @classmethod
    def types(cls, activities_in):
        activity_types = []
        if 'gigs' in activities_in:
            activity_types.append(ActivityType.GIG_POSTED.value)
            activity_types.append(ActivityType.APPLICATION_SUBMITTED.value)
            activity_types.append(ActivityType.GIG_ASSIGNED.value)
            activity_types.append(ActivityType.APPLICATION_REJECTED.value)
        if 'offers' in activities_in:
            activity_types.append(ActivityType.NEW_OFFER_POSTED.value)
            activity_types.append(ActivityType.NEW_PROPOSAL.value)
        if 'positions' in activities_in:
            activity_types.append(ActivityType.NEW_POSITION_POSTED.value)
        if 'communities' in activities_in:
            activity_types.append(ActivityType.NEW_COMMUNITY_CREATED.value)
            activity_types.append(ActivityType.NEW_MEMBER_IN_YOUR_COMMUNITY.value)
        if 'events' in activities_in:
            activity_types.append(ActivityType.NEW_EVENT_POSTED.value)
        if 'people' in activities_in:
            activity_types.append(ActivityType.NEW_EMPLOYEE_JOINED.value)
            activity_types.append(ActivityType.NEW_ROLE.value)
        if 'mentors' in activities_in:
            activity_types.append(ActivityType.NEW_MENTORSHIP_BEING_OFFERED.value)

        return activity_types


class ActivityStatus(enum.Enum):
    NEW = 'new'

    READ = 'read'
    UNREAD = 'unread'

    DELETED = 'deleted'

    @classmethod
    def lookup(cls, stat):
        try:
            return cls(stat)
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid activity status: {stat}") from ex


class Activity(ModelBase):
    __tablename__ = 'activity'

    customer = relationship("Customer")
    user = relationship("User")

    ACTIVITY_DEFAULT_START = 0
    ACTIVITY_DEFAULT_LIMIT = 20
    ACTIVITY_MAX_LIMIT = 100

    @classmethod
    def lookup(cls, tx, activity_id):
        activity = tx.query(cls).where(and_(
            cls.id == activity_id,
            cls.status != ActivityStatus.DELETED.value,
        )).one_or_none()
        if activity is None:
            raise DoesNotExistError(f"Activity '{activity_id}' does not exist")
        return activity

    @classmethod
    def add_activity(cls, user, act_type, data):
        activitytype = ActivityType.lookup(act_type)
        return Activity(
            id=str(uuid.uuid4()),
            customer=user.customer,
            user=user,
            type=activitytype.value,
            data=data,
            created_at=datetime.utcnow(),
            status=ActivityStatus.UNREAD.value
        )

    @classmethod
    def find_multiple(cls, tx, user_id, activities_in, start=None, limit=None):  # pylint: disable=too-many-arguments
        if limit is None:
            limit = cls.ACTIVITY_DEFAULT_LIMIT
        limit = min(limit, cls.ACTIVITY_MAX_LIMIT)
        if start is None:
            start = cls.ACTIVITY_DEFAULT_START

        activities = tx.query(cls).where(and_(
            cls.user_id == user_id,
            cls.status != ActivityStatus.DELETED.value
        ))

        activity_types = ActivityType.types(activities_in)
        if activity_types:
            activities = activities.where(Activity.type.in_(activity_types))

        activities = activities.order_by(Activity.created_at.desc()).offset(start).limit(limit)

        return activities.all()

    @classmethod
    def unread_count(cls, tx, user_id):
        return tx.query(func.count(cls.id)).where(and_(
            cls.user_id == user_id,
            cls.status == ActivityStatus.UNREAD.value
        )).scalar()

    def as_dict(self):
        return {
            'activity_id': self.id,
            'type': self.type,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
        }


class ActivityGlobal(ModelBase):
    __tablename__ = 'activity_global'

    customer = relationship("Customer")

    ACTIVITY_DEFAULT_START = 0
    ACTIVITY_DEFAULT_LIMIT = 20
    ACTIVITY_MAX_LIMIT = 100

    @classmethod
    def lookup(cls, tx, activity_id):
        activity = tx.query(cls).where(and_(
            cls.id == activity_id,
            cls.status != ActivityStatus.DELETED.value,
        )).one_or_none()
        if activity is None:
            raise DoesNotExistError(f"Global activity '{activity_id}' does not exist")
        return activity

    @classmethod
    def add_activity(cls, customer, act_type, data):
        activity_type = ActivityType.lookup(act_type)
        return ActivityGlobal(
            id=str(uuid.uuid4()),
            customer=customer,
            type=activity_type.value,
            data=data,
            created_at=datetime.utcnow(),
            status=ActivityStatus.NEW.value
        )

    @classmethod
    def find_multiple(cls, tx, customer_id, activities_in, start=None, limit=None):  # pylint: disable=too-many-arguments
        if limit is None:
            limit = cls.ACTIVITY_DEFAULT_LIMIT
        limit = min(limit, cls.ACTIVITY_MAX_LIMIT)
        if start is None:
            start = cls.ACTIVITY_DEFAULT_START

        activities = tx.query(cls).where(and_(
            cls.customer_id == customer_id,
            cls.status != ActivityStatus.DELETED.value
        ))

        activity_types = ActivityType.types(activities_in)
        if activity_types:
            activities = activities.where(ActivityGlobal.type.in_(activity_types))

        activities = activities.order_by(ActivityGlobal.created_at.desc()).offset(start).limit(limit)

        return activities.all()

    def as_dict(self):
        return {
            'activity_id': self.id,
            'type': self.type,
            'data': self.data,
            'created_at': self.created_at.isoformat()
        }


# Old my activities code starts here - DEPRICATED
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
